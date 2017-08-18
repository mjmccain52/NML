"""Corners Game presents targets in a set "random" order in the corners of the
screen. As the user points to each target, as long as the finger is moving 
below a certain threshold speed, that target will disappear and the next will
be presented. This continues until each possible path has been traversed a 
predetermined number of times. The data is written to a .csv file in the data 
folder.

Author: Michael McCain
Date: 10 Dec 2013

TODO:   Blit images instead of updating entire screen
        
"""
# Python libraries
from os import environ, makedirs, path
from time import strftime
from math import sqrt

# 3rd-party libraries (requires download and install)
import Leap
from easygui import enterbox, msgbox, ynbox 
from pygame import display, draw, event, init, mouse 
from pygame import quit as pgquit, time as pgtime
from pygame import  MOUSEMOTION, QUIT, USEREVENT

# Custom libraries
import nml, screen_calibration
from colors import BLACK, GREEN, RED, WHITE 
       
#
#  CONSTANTS TO CHANGE VALUES BY PREFERENCE
#

# Default filename root and folder where data will be saved. Name and timestamp
# data are added later for further uniqueness
DEFAULT_FILENAME = "corners"
DEFAULT_FOLDER = "..\\data"

THRESHOLD_SPEED = 50 # mm/s
# Distance in pixels from the edge of the screen to center of targets
DIST_FROM_EDGE_PX = 100
# Diameter of targets in mm
TARGET_SIZE = 10

CURSOR_SIZE = 7

WINDOW_SIZE_MM = int(7*25.4) 
#Refresh rate of loop in frames per second. Affects smoothness of graphics
FRAMERATE = 60

# Time to load a target, in seconds. If you use a fraction, be sure to express
# it as a float, e.g. 1/3.0 or 1.0/3 not 1/3
TARGET_LOAD_TIME = 1.0

# Indices in the locations list
NW = 0
NE = 1
SW = 2
SE = 3

TARGET_LIST = ("NW","NE","SW","SE")
# How many times each path should be traversed (1-3). For more than 3, code 
# more patterns
HITS_PER_PATH = 3

# Movement patterns, each starts and ends in the NW corner.
PATTERN = (NW,SW,NE,SE,NE,NW,SE,SW,SE,NW,NE,SW,NW)
PATTERN_2 = (NE,SW,SE,SW,NW,SE,NE,SE,NW,SW,NE,NW)
PATTERN_3 = (SW,NE,SE,NE,NW,SE,SW,SE,NW,NE,SW,NW)

# File location of exit icon
EXIT_BUTTON = "exit.png"

# Time for Mouse to disappear after movement
MOUSE_TIMER = 3

class Circle:
    """Simple object to store position and radius
    """
    def __init__(self, position, radius):
        """Sets up Circle with initial values.
        
        Args:
            position (tuple<int>):  Coordinates for the center of the circle 
                                    (x,y).
            radius (int):           Value for the radius of the circle.
        """
        self.position = position
        self.radius = radius
    
class ClockLeapListener(Leap.Listener):
    """ An activated instance of ClockLeapListener will be able to interrupt
    any process in progress to run its own if it sense input.
    """


    def on_init(self, controller):
        """ Sets up the Listener with some initial values/flags.
        
        Args:
            controller (Leap.Controller):    Activated Leap Controller
        """
        # Cursor position
        self.cur_x = 0
        self.cur_y = 0
        self.first = True # Flag signaling the first frame of data
    def move_mouse(self, x, y, speed, zf):
        """Updates the hand cursor position and size

        Args:
            x (int):     Horizontal position, in pixels, from left of graphics window
            y (int):     Vertical position, in pixels, from top of graphics window
            zf (float):  Depth factor to determine how big the cursor is
        """
        global screen
        global cursor
        if self.cur_x != x or self.cur_y != y:      
            self.cur_x = x
            self.cur_y = y
            rad = CURSOR_SIZE + int(zf)
            if rad <= 0:
                rad = 1
            cursor = Circle((int(x),int(y)),rad)
            event.post(event.Event(USEREVENT, {'pos':(x,y),'speed':speed}))
            
    def on_frame(self, controller):
        """Runs every time the Leap detects interaction, anywhere from 50 to 200
        frames per second.

        Args:
            controller (Leap.Controller): Leap controller object that had this 
                                          listener instance added to it.
        """
        frame = controller.frame()
        
        # On first frame, establishes start time
        if self.first:
            self.startup = frame.timestamp/1000.0
            self.first = False
        global screen_x
        global screen_y
        global cursor
        if not frame.fingers.is_empty:
            fingers = frame.fingers
            row = [frame.timestamp/1000.0 - self.startup,TARGET_LIST[currentTarget]]
            v = fingers[0].tip_velocity
            speed = sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2])
            row.append(speed)
            row.extend(nml.finger_positions_to_list(fingers))
            
            data.append(row)
            pos = fingers[0].tip_position
            xy = cal_data.finger_to_graphics(pos, (win_size_px, win_size_px))
            zFactor = fingers[0].tip_position[2] / -20.0
            v = fingers[0].tip_velocity
            speed = sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2])
            self.move_mouse(xy[0], xy[1], speed, zFactor)
        
def initialize_graphics():
    """Set up the game screen, which gets WINDOWS system data for fullscreen.
    Determine based on the screen resolution where the targets will be located.
    """
    environ['SDL_VIDEO_CENTERED'] = '1'
    init() #Initialize game engine
    global screen
    global locations
    # Get the monitor dimensions for fullscreen and Leap pointing
    screen_size = (win_size_px,win_size_px)
    screen = display.set_mode(screen_size)
    display.set_caption("DO NOT MOVE THIS WINDOW")
    
    # Target locations: (NW, NE, SW, SE)
    locations = [(DIST_FROM_EDGE_PX, DIST_FROM_EDGE_PX), (win_size_px - DIST_FROM_EDGE_PX, DIST_FROM_EDGE_PX), \
             (DIST_FROM_EDGE_PX, win_size_px - DIST_FROM_EDGE_PX), (win_size_px - DIST_FROM_EDGE_PX, win_size_px - DIST_FROM_EDGE_PX)]

def is_in_target(position, target):
    """Determine whether the position of the mouse lies within the target
    using Pythagorean Theorem

    Args:
        position (tuple<int>): position of cursor (x,y)
        target (tuple<int>):   position of current target (x,y)
    Returns:
        True if position is in target, False otherwise
    """
    x, y = position[0], position[1]
    center_x, center_y = target[0], target[1]
    return (x - center_x)**2 + (y - center_y)**2 <= TARGET_SIZE**2

def update_screen(target, load=None, cursor=None):
    """Redraw the screen with the new locations of targets, cursor, etc.

    Args:
        target (Circle): Current target
        load (Circle):   Green loading circle in target
        cursor (Circle): The finger-controlled red cursor
    """
    global screen
    screen.fill(WHITE) # Background
    draw.circle(screen, BLACK, target.position, target.radius) # Target
    if load:
        draw.circle(screen, GREEN, load.position, load.radius) # Loading
    if cursor:
        draw.circle(screen, RED, cursor.position, cursor.radius) # Cursor
    #screen.blit(exit_image, (win_size_px - img_rect.w, 0)) # Exit button
    display.flip() # Refreshes screen
    
#
# PROGRAM STARTS RUNNING HERE
#
cal_data = screen_calibration.CalibrationData()
if not cal_data.load_calibration():
    cal_data = screen_calibration.auto_calibration()
    cal_data.save_calibration()
else:
    if ynbox("Calibration file found. Recalibrate screen anyway?"):
        cal_data = screen_calibration.auto_calibration()
        cal_data.save_calibration()

ppmm = cal_data.ppmm
TARGET_SIZE = int(TARGET_SIZE * ppmm/2)
win_size_px = int(WINDOW_SIZE_MM*ppmm)
# Establish the pattern. Usually only 1 or 2 during debugging for convenience
pattern = PATTERN
if HITS_PER_PATH >= 2:
    pattern += PATTERN_2
if HITS_PER_PATH >= 3:
    pattern += PATTERN_3

# Get name from user for use in the filename
name = enterbox("Please enter your last name (no spaces)","Name Entry")
if name == None:
    name = ""
    
# Display instructions
msgbox("Corners Game Data Logger\nBYU Neuromechanics Lab 2013\n\n" + \
       "This application will track and log data from a single finger. Use a " + \
       "single index finger to point at the screen. A red cursor will track" +\
       " the motion. Black targets will be displayed, appearing in random "+\
       "order in each corner of the window. Point at targets as they appear. "+\
       "To exit before the test is completed, use the mouse to click the X"+\
       " in the upper right corner of the window.\nPress OK to start.",
       "BYU NML Corners")
        
practice = ynbox("Do you want a practice run?")


while True:
    run_timestamp = strftime("%Y%m%d%H%M%S") # data file will have unique
                                            # with the date and time
    #data starts empty each run and is global for access by the listener
    global data
    data = []
    
    initialize_graphics()
    listener = ClockLeapListener()
    controller = Leap.Controller()
    controller.add_listener(listener)
    
    # How many frames an unmoving mouse will stay visible
    mouse_frames = int (FRAMERATE * MOUSE_TIMER)
    mouse_frames_count = 0
    mouse.set_visible(False)
    
    clock = pgtime.Clock() # clock is used to control framerate in the loop
    
    # Draw first target in the center of the screen
    currentTarget = NW
    #drawTarget(currentTarget, clear=True)
    ct = Circle(locations[NW], TARGET_SIZE)
    
    # Various flag/progress values
    mouse_on = False
    motion_bug = True   # When the mouse disappears, it moves back to the center
                        # of the screen, this technically qualifies as mouse
                        # movement. This flag is to negate that effect
    done = False
    #load_circle = None
    global cursor
    cursor = None
    update_screen(ct)
    increment = 0 # current radius of a loading circle
    step = 0 # Current step of the pattern
    
    # Loop until the exit signal is given
    while not done:   
        update = False

        # Cycles through list of user actions (mouse motion, clicks, hand 
        # motion, etc.) per frame   
        for e in event.get(): 
            # User sends shutdown signal
            if e.type == QUIT:
                done = True

            # Mouse is moving or finger is in Leap range (Custom-defined USEREVENT
            # above)
            elif e.type == USEREVENT:
                update = True
                if is_in_target(e.pos, locations[currentTarget]) and e.speed < 100:
                    step += 1
                    if step == len(pattern):
                        done = True
                        break
                    update = True
                    increment = 0            
                    currentTarget = pattern[step]       
                    ct.position = locations[currentTarget]

            # If user moves the mouse, start the frame count and signal that 
            # the mouse is showing
            if e.type == MOUSEMOTION:
                if not motion_bug:
                    mouse.set_visible(True)
                    mouse_on = True
                    mouse_frames_count = 0
                else:
                    motion_bug = False
        # An event may have signaled that it's time to redraw the screen
        if update:
            update_screen(ct, None, cursor)
        
        # If the mouse is showing, progress the frame count and make it
        # disappear if it's been long enough
        if mouse_on:
            mouse_frames_count += 1
            if mouse_frames_count >= mouse_frames:
                mouse.set_visible(False)
                motion_bug = True
                mouse_on = False
                mouse_frames_count = 0
                
        clock.tick(FRAMERATE) # Limits framerate of loop

    controller.remove_listener(listener) # Makes the Leap stop gathering data
    pgquit() # Be IDLE friendly by formally quitting game engine
    
    
    if (ynbox("Do you want to record these results?")):
        # Create a folder for the data if it's not there
        if not path.exists(DEFAULT_FOLDER):
            makedirs(DEFAULT_FOLDER)
        filename = DEFAULT_FOLDER + "\\" + DEFAULT_FILENAME + "_"+ name + "_" + run_timestamp + ".csv"
        writeFile = open(filename, 'w')
        writeFile.write ('Time (ms),Target,Speed (mm/s),Position Data for Clock Game(mm)\n' + \
                         ',,,x,y,z\n')
        # Write the gathered data to file
        for row in data:
            for element in row:
                writeFile.write(str(element) + ',')
            writeFile.write('\n')
        writeFile.close()
    
    # Prompt for repeats
    msg = "Do you want to run the program again?"
    title = "One more go?"
    if not ynbox(msg, title):
        break

