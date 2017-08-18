"""Corners Game presents targets in a set "random" order in the corners of the
screen. As the user points to each target, as long as the finger is moving 
below a certain threshold speed, that target will disappear and the next will
be presented. This continues until each possible path has been traversed a 
predetermined number of times. The data is written to a .csv file in the data 
folder.

Changes from v1_7:
        -Animation using "Dirty Rect" technique
        
Author: Michael McCain
Date: 15 Jan 2014

TODO:  
        -Fix cursor size factors
        -Make gray inactive targets
        -Write "main"(?)
        -Use on_frame() only for datalogging (?)
        -Update only specific portions of the screen to improve smoothness       
"""
# Python libraries
from os import environ, makedirs, path
from time import strftime, time as timetest
from math import sqrt
from sys import exit

# 3rd-party libraries
import Leap
from easygui import enterbox, msgbox, ynbox 
from pygame import display, event, init, mouse, image, transform, Rect
from pygame import quit as pgquit, time as pgtime
from pygame import  MOUSEMOTION, QUIT, USEREVENT

# Custom libraries
import screen_calibration
from colors import WHITE 

# True to skip directly to game, False to run the entire program
GAME_TEST = True
# Conversion from inches to mm
IN_MM = 25.4 # mm per inch
# Default filename root and folder where data will be saved.
DEFAULT_FILENAME = "corners"
DEFAULT_FOLDER = "..\\data"
# The user must be moving below this speed to trigger targets
THRESHOLD_SPEED = 50 # mm/s
# Distance from the edge of the screen to center of targets
DIST_FROM_EDGE_PX = 100 # pixels
# Diameter of targets
TARGET_DIA_MM = 10 # mm
# Length of each side of the square interaction window
WINDOW_SIZE_MM = int(5*IN_MM) # mm
# Refresh rate of graphics loop. Affects smoothness of graphics
FRAMERATE = 60 # frames per second
# Indices in the locations list
NW = 0
NE = 1
SW = 2
SE = 3
# List of locations in string format for writing data to file
TARGET_LIST = ("NW","NE","SW","SE")
# The squence in which the user sees targets.
PRACTICE_PATTERN = (NW,SW,NE,SE,NE,NW,SE,SW,SE,NW,NE,SW,NW)
PATTERN = (NW,SW,NE,SE,NE,NW,SE,SW,SE,NW,NE,SW,NW,NE,SW,SE,SW,NW,SE,NE,SE,NW,
           SW,NE,NW,SW,NE,SE,NE,NW,SE,SW,SE,NW,NE,SW,NW)
# Time for Mouse to disappear after movement
MOUSE_TIMER = 3 # seconds

previous_loc = None

class Circle:
    """Simple object to store position and radius"""
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
   
    def move_mouse(self, x, y, z, speed):
        """Updates the hand cursor position and size

        Args:
            x (int):         Horizontal position, in pixels, from left of graphics
                             window
            y (int):         Vertical position, in pixels, from top of graphics 
                             window
            z (float):       Depth position, in millimeters, from center of Leap
            speed (float):   Current fingertip speed, in millimeters/second 
        """
        global cursor, previous_loc
        if self.cur_x != x or self.cur_y != y:
            #if cursor:
            #   previous_loc = Circle(cursor.position,cursor.radius)  
            self.cur_x = x
            self.cur_y = y
            # This equation matches the radius of the cursor to the sizes of
            # the near and far targets when the user moves in and out
            rad = target_radius_px-int(z)
            if rad <= 0: # Prevents negative radius
                rad = 1
            cursor = Circle((int(x),int(y)),rad)
            # Puts a custom event onto Pygame's event queue to be accessed
            # when looping through all events.
            event.post(event.Event(USEREVENT, {'pos':(x,y,z),'speed':speed}))
            
    def on_frame(self, controller):
        """Runs every time the Leap detects interaction, anywhere from 50 to 
        200 frames per second.

        Args:
            controller (Leap.Controller): Leap controller object that had this 
                                          listener instance added to it.
        """
        frame = controller.frame()
        
        # On first frame, establishes start time
        if self.first:
            self.startup = frame.timestamp/1000.0 # Converts to milliseconds
            self.first = False

        if not frame.fingers.is_empty:
            fingers = frame.fingers
            row = [frame.timestamp/1000.0 - self.startup,
                   TARGET_LIST[target_index]]
            v = fingers[0].tip_velocity
            speed = sqrt(v[0]**2+v[1]**2+v[2]**2)
            row.append(speed)
            finger_list = []
            for finger in fingers:
                # Vectors from the Leap API must be converted to python arrays
                finger_list.extend(finger.tip_position.to_float_array())
            row.extend(finger_list)
            
            data.append(row)
            pos = fingers[0].tip_position
            # Custom function turns real space coordinates into matching pixels
            xy = cal_data.finger_to_graphics(pos, (win_size_px, win_size_px))
            self.move_mouse(xy[0], xy[1], pos[2], speed)#, zFactor)
        
def initialize_graphics():
    """ Set up the game screen, which gets WINDOWS system data for fullscreen.
    Determine based on the screen resolution where the targets will be located.
    """
    environ['SDL_VIDEO_CENTERED'] = '1'
    init() #Initialize game engine
    global screen
    global locations
    screen = display.set_mode((win_size_px,win_size_px))
    display.set_caption("DO NOT MOVE THIS WINDOW")
    global black_target
    global red_cursor
    global gray_target
    black_target = image.load("black.png").convert_alpha()
    red_cursor = image.load("red.png").convert_alpha()
    # Target locations: (NW, NE, SW, SE)
    locations = [(DIST_FROM_EDGE_PX, DIST_FROM_EDGE_PX),
                 (win_size_px - DIST_FROM_EDGE_PX, DIST_FROM_EDGE_PX),
                 (DIST_FROM_EDGE_PX, win_size_px - DIST_FROM_EDGE_PX), 
                 (win_size_px - DIST_FROM_EDGE_PX, win_size_px - DIST_FROM_EDGE_PX)]
    screen.fill(WHITE)
    logo = image.load("Neuromechanics Logo 50.png").convert()
    logo_rect = logo.get_rect(center=(win_size_px/2,win_size_px/2))
    screen.blit(logo,logo_rect)
    #screen.blit(logo,(win_size_px/2 - logo.get_rect().width/2,
    #                  win_size_px/2 - logo.get_rect().height/2))

    display.flip()


def is_in_target(position, target):
    """ Determine whether the position of the mouse lies within the target
    using Pythagorean Theorem

    Args:
        position (tuple<int>): position of cursor (x,y,z)
        target (tuple<int>):   position of current target (x,y,z)
    Returns:
        True if position is in target, False otherwise
    """
    x, y = position[0], position[1]
    center_x, center_y = target[0], target[1]
    return (x - center_x)**2 + (y - center_y)**2 <= target_radius_px**2

def update_screen(target, cursor=None):
    """Redraw the screen with the new locations of targets, cursor, etc.

    Args:
        target (Circle): Current target
        cursor (Circle): The finger-controlled red cursor
    """
    global screen
    global black_target
    global red_cursor
    global previous_loc
    dirty_rects = []
    #screen.fill(WHITE) # Background
    #logo = image.load("Neuromechanics Logo 50.png").convert()
    #screen.blit(logo,(win_size_px/2 - logo.get_rect().width/2,
    #                 win_size_px/2 - logo.get_rect().height/2))
    # Target
    
    temp_black = black_target
    logo = image.load("Neuromechanics Logo 50.png").convert()
    logo_rect = logo.get_rect(center=(win_size_px/2,win_size_px/2))
    
    temp_black = transform.scale(temp_black, (target.radius*2,target.radius*2))
    black_rect = temp_black.get_rect(center=target.position[0:2])
    #screen.blit(temp_black,(tx,ty))
    
    # Cursor
    if cursor:
        if previous_loc:
            screen.fill(WHITE, previous_loc)
            screen.blit(logo,logo_rect)
            screen.blit(temp_black,black_rect)
            dirty_rects.append(previous_loc)
            dirty_rects.append(logo_rect)
            dirty_rects.append(black_rect)
        temp_red = red_cursor
        temp_red = transform.scale(temp_red, (cursor.radius*2,cursor.radius*2))
        red_rect = temp_red.get_rect(center=cursor.position[0:2])
        previous_loc = temp_red.get_rect(center=cursor.position[0:2])
        screen.blit(temp_red,red_rect)
        dirty_rects.append(red_rect)
    
    #display.flip() # Refreshes screen
    display.update(dirty_rects)
    
def write_to_file(name, timestamp, hand, trial):
    """ Write data from a single iteration to file.

    Args:
        name (str):      Last name of subject
        timestamp (str): Time at the beginning of the test - YYYYMMDDHHmm
        hand (str):      Left or Right
        trial (str):     1 or 2
    """
    # Create a folder for the data if it's not there
    if not path.exists(DEFAULT_FOLDER):
        makedirs(DEFAULT_FOLDER)
    filename = DEFAULT_FOLDER + "\\" + DEFAULT_FILENAME + "_"+ name + "_" + \
               timestamp + "_" + hand + trial + ".csv"
    writeFile = open(filename, 'w')
    # In the .csv, date is recorded in the format MM/DD/YYYY
    date = strftime("%m") + "/" + strftime("%d") + "/" + strftime("%Y")
    writeFile.write ('Subject:,' + name +',Hand:,' + hand + ',Date:,' + date + 
                     '\nTime (ms),Target,Speed (mm/s),Position (mm)\n'
                     ',,,x,y,z\n')
    # Write the gathered data to file
    for row in data:
        for element in row:
            writeFile.write(str(element) + ',')
        writeFile.write('\n')
    writeFile.close()
    
def main_game(pattern):
    """ Displays the graphics window with the targets and displays targets 
    through the end of the pattern.

    Args:
        pattern (tuple<int>): The sequence of target locations to be displayed
    """
    global data
    global target_index
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
    target_index = PATTERN[0]
    current_target = Circle(locations[target_index], target_radius_px)
    
    # Various flag/progress values
    mouse_on = False
    # When the mouse disappears, it moves back to the center of the screen, 
    # this technically qualifies as mouse movement. This flag is to negate 
    # that effect.
    motion_bug = True   
    done = False
    #load_circle = None
    global cursor
    cursor = None
    update_screen(current_target)
    step = 0 # Current step of the pattern
    
    # Loop until the exit signal is given
    while not done:
        before = timetest()    
        update = False

        # Cycles through list of user actions (mouse motion, clicks, hand 
        # motion, etc.) per frame   
        for e in event.get(): 
            # User sends shutdown signal
            if e.type == QUIT and ynbox("Are you sure you want to quit?"):
                controller.remove_listener(listener)
                pgquit()
                exit()

            # Finger is in Leap range (Custom-defined USEREVENT above)
            elif e.type == USEREVENT:
                update = True
                if is_in_target(e.pos, locations[target_index]) \
                   and e.speed < THRESHOLD_SPEED:
                    step += 1
                    if step == len(pattern):
                        done = True
                        break
                    update = True       
                    target_index = pattern[step]       
                    current_target.position = locations[target_index]

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
            
            update_screen(current_target, cursor) #.01 seconds
            print timetest()-before
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
    
######## START OF PROGRAM ###########      

# data file will have unique with the date and time      
run_timestamp = strftime("%Y%m%d%H%M") 
cal_data = screen_calibration.CalibrationData()
if not cal_data.load_calibration():
    cal_data = screen_calibration.auto_calibration()
    cal_data.save_calibration()
else:
    if ynbox("Screen calibration file found. Recalibrate screen anyway? (This "
             "is a good idea if the Leap Motion Controller has been bumped or "
             "moved since you last used it", "Screen Calibration"):
        cal_data = screen_calibration.auto_calibration()
        cal_data.save_calibration()

ppmm = cal_data.ppmm
target_radius_px = int(TARGET_DIA_MM * ppmm/2.0)
win_size_px = int(WINDOW_SIZE_MM*ppmm)

# Skips instructions and repeats if just testing out the program
if GAME_TEST:
    main_game(PRACTICE_PATTERN)
    exit()
    
# Get name from user for use in the filename
name = enterbox("Please enter your last name (no spaces)","Name Entry")
if name == None:
    name = ""
    
msgbox("Corners Game Data Logger\nBYU Neuromechanics Research Group 2013\n\n"
       "This application will track and log data from a single finger. Use a " 
       "single index finger to point at the screen. A red cursor will track "
       "the motion. Black targets will be displayed, appearing in random "
       "order in each corner of the window. Point at targets as they appear. "
       "To exit the application before the test is completed, close the "
       "window of the main program once it starts.\nPress OK to start.",
       "BYU NRG Corners")

if ynbox("Do you want a practice run?"):
    msgbox("Short practice run with your right hand. Press OK")
    main_game(PRACTICE_PATTERN)
    msgbox("Rest for up to 90 seconds, then press OK to practice with "
           "left hand")
    main_game(PRACTICE_PATTERN)
    msgbox("Take another 90 second break, then press OK to proceed with "
           "the actual test.")
msgbox("Use your right hand to point to the targets as they appear. Press "
       "OK to begin.")
main_game(PATTERN)
write_to_file(name, run_timestamp, "right", "1")
msgbox("Rest for up to 2 minutes, then repeat the exercise using your "
       "left hand. Press OK to begin.")
main_game(PATTERN)
write_to_file(name, run_timestamp, "left", "1")
msgbox("Rest for up to 2 minutes, then repeat the exercise using your "
       "right hand. Press OK to begin.")
main_game(PATTERN)
write_to_file(name, run_timestamp, "right", "2")
msgbox("Rest for up to 2 minutes, then repeat the exercise using your "
       "left hand. Press OK to begin.")
main_game(PATTERN)
write_to_file(name, run_timestamp, "left", "2")
    
msgbox("All tests completed. Thank you.")

