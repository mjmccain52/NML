"""Corners Game presents targets in a set "random" order in the corners of the
screen. As the user points to a target, the target will "load" for a moment to
pause the user's motion, then disappear and the next target will be presented.
This continues until each possible path has been traversed a predetermined
number of times. The data is written to a .csv file in the data folder.

Author: Michael McCain
Date: 7 Nov 2013

TODO:   Blit images instead of updating entire screen
        Calibrate monitor (unsupported as of 11/7/13)
        Make window uniform size
        
"""
import Leap, nml, screen_calibration
from colors import BLACK, GREEN, RED, WHITE 
from ctypes import windll
from easygui import enterbox, msgbox, ynbox 
from os import makedirs, path 
from pygame import display, draw, event, image, init, mouse 
from pygame import quit as pgquit, time as pgtime
from pygame import FULLSCREEN, MOUSEBUTTONDOWN, MOUSEMOTION, QUIT, USEREVENT       
from time import strftime


#
#  CONSTANTS TO CHANGE VALUES BY PREFERENCE
#

# Default filename root and folder where data will be saved. Name and timestamp
# data are added later for further uniqueness
DEFAULT_FILENAME = "corners"
DEFAULT_FOLDER = "..\\data"

# Distance in pixels from the edge of the screen to center of targets
DIST_FROM_EDGE_PX = 100
# Diameter of targets in mm
TARGET_SIZE = 10

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
    def move_mouse(self, x, y, zf):
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
            rad = 15 + int(zf)
            if rad <= 0:
                rad = 1
            cursor = Circle((int(x),int(y)),rad)
            event.post(event.Event(USEREVENT, {'pos':(x,y)}))
            
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
            row = [frame.timestamp/1000.0 - self.startup]
            row.extend(nml.finger_positions_to_list(fingers))
            data.append(row)
            pos = fingers[0].tip_position
            xy = cal_data.finger_to_graphics(pos, (screen_x, screen_y))
            zFactor = fingers[0].tip_position[2] / -20.0
            self.move_mouse(xy[0], xy[1], zFactor)
        
def initialize_graphics():
    """Set up the game screen, which gets WINDOWS system data for fullscreen.
    Determine based on the screen resolution where the targets will be located.
    """
    init() #Initialize game engine
    global screen
    global screen_x
    global screen_y
    global locations
    
    # Get the monitor dimensions for fullscreen and Leap pointing
    user32 = windll.user32
    screen_x = user32.GetSystemMetrics(0)
    screen_y = user32.GetSystemMetrics(1)
    screen_size = (screen_x,screen_y)
    screen = display.set_mode(screen_size,FULLSCREEN)
    display.set_caption("Clock Game")
    
    # Target locations: (NW, NE, SW, SE)
    locations = [(DIST_FROM_EDGE_PX, DIST_FROM_EDGE_PX), (screen_x - DIST_FROM_EDGE_PX, DIST_FROM_EDGE_PX), \
             (DIST_FROM_EDGE_PX, screen_y - DIST_FROM_EDGE_PX), (screen_x - DIST_FROM_EDGE_PX, screen_y - DIST_FROM_EDGE_PX)]

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
    screen.blit(exit_image, (screen_x - img_rect.w, 0)) # Exit button
    display.flip() # Refreshes screen

#
# PROGRAM STARTS RUNNING HERE
#
cal_data = screen_calibration.CalibrationData()
if not cal_data.load_calibration():
    cal_data = screen_calibration.auto_calibration()
    cal_data.save_calibration()


ppmm = cal_data.ppmm
TARGET_SIZE = int(TARGET_SIZE * ppmm/2)
# Establish the pattern. Usually only 1 or 2 during debugging for convenience
pattern = PATTERN
if HITS_PER_PATH >= 2:
    pattern += PATTERN_2
if HITS_PER_PATH >= 3:
    pattern += PATTERN_3

# Load the exit button
exit_image = image.load(EXIT_BUTTON)
img_rect = exit_image.get_rect() 

# Get name from user for use in the filename
name = enterbox("Please enter your last name (no spaces)","Name Entry")
if name == None:
    name = ""
    
# Display instructions
msgbox("Corners Game Data Logger\nBYU Neuromechanics Lab 2013\n\n" + \
       "This application will track and log data from a single finger. Use a " + \
       "single index finger to point at the screen. A red cursor will track" +\
       " the motion. Black targets will be displayed, appearing in random "+\
       "order in each corner of the screen. Point at targets as they appear "+\
       " using the red cursor. Pause for a moment in each target while the green " +\
       "circle loads, then proceed to the next target. To exit before the test "+\
       "is completed, use the mouse to click the exit icon in the upper right.", "BYU NML Corners")


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
    load_circle = None
    global cursor
    cursor = None
    update_screen(ct)
    increment = 0 # current radius of a loading circle
    step = 0 # Current step of the pattern
    
    # Loop until the exit signal is given
    while not done:   
        update = False

        # Progresses green loading circle if hovering in a target
        if load_circle and not load_circle.radius >= TARGET_SIZE:
            update = True
            if TARGET_LOAD_TIME == 0:
                load_circle.radius = TARGET_SIZE;
            else:
                increment += TARGET_SIZE / float(FRAMERATE * TARGET_LOAD_TIME)
                load_circle.radius = int(increment) # Loading circle gets bigger by tenths

        # If green circle is fully loaded, draw the next target in the pattern
        elif load_circle and load_circle.radius >= TARGET_SIZE:
            step += 1
            if step == len(pattern):
                break
            update = True
            increment = 0
            load_circle = None
            
            currentTarget = pattern[step]       
            ct.position = locations[currentTarget]


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
                # Toggle loading if cursor is in target
                if is_in_target(e.pos, locations[currentTarget]):
                    if not load_circle:
                        load_circle = Circle(ct.position,0)

                # Reset loading if cursor leaves target
                elif load_circle:
                    increment = 0
                    load_circle = None
            # Exit if user clicks the exit button
            elif e.type == MOUSEBUTTONDOWN and e.button == 1 \
                and e.pos[0] > screen_x - img_rect.w and e.pos[1] < img_rect.h:
                done = True
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
            update_screen(ct, load_circle, cursor)
        
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
    
    # Create a folder for the data if it's not there
    if not path.exists(DEFAULT_FOLDER):
        makedirs(DEFAULT_FOLDER)
    filename = DEFAULT_FOLDER + "\\" + DEFAULT_FILENAME + "_"+ name + "_" + run_timestamp + ".csv"
    writeFile = open(filename, 'w')
    writeFile.write ('Time (ms),Position Data for Clock Game(mm)\n' + \
                     ',x,y,z\n')
    # Write the gathered data to file
    for row in data:
        for element in row:
            writeFile.write(str(element) + ',')
        writeFile.write('\n')
    writeFile.close()
    
    # Prompt for repeats
    msg = "Do you want to run the program again?"
    title = "One more go?"
    choice = ynbox(msg, title)
    if choice == 0:
        break

