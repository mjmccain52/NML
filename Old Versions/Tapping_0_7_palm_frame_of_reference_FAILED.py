""" Application that counts the number of times a single finger wags up and
down past defined thresholds using the Leap Motion

Changes from v0_6:
        -Added trial rejection if base of the finger moves too much
Author: Michael McCain
Date: 21 Jan 2014

TODO:  
        -Add detection for wrist instead of finger motion
        -Blit images instead of updating entire screen to hopefully make 
         smoother motion.       
"""
# Python libraries
from time import clock, strftime
from os import path, makedirs, environ
# 3rd-party libraries
import pygame, Leap
from easygui import msgbox, enterbox,ynbox
# Custom libraries
import screen_calibration
from colors import BLACK, WHITE, BLUE

# Length of time for each trial
DEFAULT_TIMER = 10 # seconds
# Default base of filename and save location
DEFAULT_FILENAME = "tapping"
DEFAULT_FOLDER = "..\\data"
# Maximum allowable difference between trials
MARGIN = 5
# Required consecutive successful trials
SUCCESSES = 3
# Height of armrest
REST_HEIGHT_MM = int(7*25.4)  # mm
# Maximum movement allowed by the base of the finger
ALLOWABLE_BASE_MOVEMENT = 50 # mm
# Cursor Size
CURSOR_PX = 15
# Font Size
FONT_SIZE_PX = 20
# Window Size
WINDOW_SIZE_MM = int(6*25.4)
# Distance required to tap 
GAP_MM = 15 #mm



class TapListener(Leap.Listener):
    """Once activated, listens for any Leap input, interrupting any current
    process.
    """

    def on_init(self, controller):
        """ Sets up the Listener by initializing an empty data set.
        
        Args:
            controller (Leap.Controller):    Activated Leap Controller
        """
        self.data = []
    def on_frame(self, controller):
        """Runs every time the Leap detects interaction, anywhere from 50 to 
        200 frames per second.

        Args:
            controller (Leap.Controller): Leap controller object that had this 
                                          listener instance added to it.
        """
        
        global start # Time of initial recording
        frame = controller.frame() # Grab current frame of Leap data 

        # If hand and fingers are visible, record timestamp and y-position
        # for each finger.
        fingers = frame.fingers
        if not fingers.is_empty:
            frame_data = [clock() - start] # Row to be added to y_data
            finger_list = []
            for finger in fingers:
                finger_list.extend(finger.tip_position.to_float_array())
            frame_data.extend(finger_list)
            self.data.append(frame_data)

#
# PROGRAM STARTS RUNNING HERE
#
cal_data = screen_calibration.CalibrationData()
if not cal_data.load_calibration():
    msgbox("Please place the Leap Motion Controller in front of your screen.")
    cal_data = screen_calibration.auto_calibration()
    cal_data.save_calibration()
else:
    if ynbox("Calibration file found. Recalibrate screen anyway? (Necessary "
             "only if your last calibration was not on this monitor)"):
        msgbox("Please place the Leap Motion Controller in front of your"
               " screen.")
        cal_data = screen_calibration.auto_calibration()
        cal_data.save_calibration()
        msgbox("Please place the Leap Motion Controller back in front of the "
               "armrest.")

ppmm = cal_data.ppmm
win_size_px = int(WINDOW_SIZE_MM*ppmm)
name = enterbox("Please enter your last name (no spaces)","Name Entry")
if name == None:
    name = ""
TOP_LINE = int(win_size_px/2 - GAP_MM/2*ppmm)
BOT_LINE = int(win_size_px/2 + GAP_MM/2*ppmm)
#BOT_LINE = int((TOP_LINE+GAP_MM)*ppmm)
#TOP_LINE = int(TOP_LINE*ppmm)                
msgbox( "This application will track and log data from a single finger as you"
        " quickly wag it up and down above the sensor for a set period of "
        "time.", "Finger Tapping Data Logger")
all_trials = []
all_data = []
trials =[]
datalog = []
high = None
low = None
# Determine whether to use program defaults or user values
environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
run_timestamp = strftime("%Y%m%d%H%M%S")
low_base = None
high_base = None
base_movement = False
while len(trials) < SUCCESSES:    
    
    frame_clock = pygame.time.Clock()
    controller = Leap.Controller()
    listener = TapListener()
    
    running = True
    counter = 0
    past_down = False
    first = True
    ready = False
    start = 0
    frame = controller.frame()
    
    screen = pygame.display.set_mode((win_size_px,win_size_px))
    pygame.display.set_caption("Tapping")
    screen.fill(WHITE)
    while running:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT:
                controller.remove_listener(listener)
                pygame.quit()
                exit()
        frame = controller.frame()

        screen.fill(WHITE)
        pygame.draw.line(screen, BLACK, (win_size_px/2-10, win_size_px/2),
                         (win_size_px/2+10, win_size_px/2))
        pygame.draw.line(screen, BLACK, (win_size_px/2, win_size_px/2-10),
                         (win_size_px/2, win_size_px/2+10))
        pygame.draw.line(screen, BLUE, (0, TOP_LINE),(win_size_px, TOP_LINE))
        pygame.draw.line(screen, BLUE, (0, BOT_LINE),(win_size_px, BOT_LINE))
        
        # Writing text on the screen is surprisingly complex
        font = pygame.font.Font(None, FONT_SIZE_PX)
        text = font.render("Trial #"+str(len(all_trials)+1)+", taps: " + 
                           str(counter), 1, BLACK)
        textpos = text.get_rect()
        textpos.center = (win_size_px/2,20)
        screen.blit(text, textpos)
        
        if len(frame.hands) > 0:
            hand = frame.hands[0]
            handXBasis =  hand.palm_normal.cross(hand.direction).normalized
            handYBasis = -hand.palm_normal
            handZBasis = -hand.direction
            handOrigin =  hand.palm_position
            handTransform = Leap.Matrix(handXBasis, handYBasis, handZBasis, handOrigin)
            handTransform = handTransform.rigid_inverse()

            if len(hand.fingers) > 0:
                finger = hand.fingers[0]
                transformedPosition = handTransform.transform_point(finger.tip_position)
                transformedDirection = handTransform.transform_direction(finger.direction)
                tp = transformedPosition
                finger = frame.fingers[0]
                
                pos = finger.tip_position
                
                xy = (int(pos[0]*ppmm + win_size_px/2), 
                      int(REST_HEIGHT_MM*ppmm - pos[1]*ppmm + win_size_px/2))
                xy = (int(tp[0]*ppmm + win_size_px/2), 
                      int(-tp[1]*ppmm + win_size_px/2))
                print xy
                pygame.draw.circle(screen, BLACK, xy, CURSOR_PX)
                if first and xy[1] < TOP_LINE:
                    first = False
                    ready = True
         
                if xy[1] > BOT_LINE and ready:
                    ready = False
                    start = clock()
                    controller.add_listener(listener)
                if counter > 1:
                    base_pos = -finger.direction*finger.length + finger.tip_position
                    if low_base == None:
                        low_base = base_pos[1]
                        high_base = base_pos[1]
                    elif base_pos[1] < low_base:
                        low_base = base_pos[1]
                    elif base_pos[1] > high_base:
                        high_base = base_pos[1]
                    if low_base != None and \
                       high_base - low_base > ALLOWABLE_BASE_MOVEMENT:
                        base_movement = True
                        msgbox("Please move only your pointer finger for accurate"
                               " measurements")
                        break
                        
                    
                    
                if xy[1] > BOT_LINE and not first and not past_down:
                    past_down = True
                    counter +=1
                if xy[1] < TOP_LINE and past_down:
                    past_down = False
                if start > 0 and clock() - start > DEFAULT_TIMER:
                    break
                
    
    
        pygame.display.flip()
            
        frame_clock.tick(60)

    controller.remove_listener(listener)

    msg = "Finished trial"
    if len(trials) == 0:
        high = counter
        low = counter
    for trial in trials:
        if counter < low:
            low = counter
        if counter > high:
            high = counter
    if high - low > MARGIN or base_movement:
        msg += " unsuccessfully. Starting over"
        trials = []
        datalog = []
        high = counter
        low = counter
        high_base = None
        low_base = None
        base_movement = False
        
    all_trials.append(counter)
    all_data.append(listener.data)
    trials.append(counter)
    datalog.append(listener.data)
    if len(all_trials) == 10 and len(trials) < SUCCESSES:
        datalog = all_data
        trials = all_trials
        break
    msgbox(msg)
my_sum = 0
for c in trials:
    my_sum += c
avg = my_sum/len(trials)

msgbox("Trials completed.\n Average: " + str(avg))
# Create a folder for the data if it's not there
if not path.exists(DEFAULT_FOLDER):
    makedirs(DEFAULT_FOLDER)
for i in range(len(datalog)):
    filename = DEFAULT_FOLDER + "\\" + DEFAULT_FILENAME + "_"+ name + "_" + \
               run_timestamp + "_"+str(i)+".csv"
    writeFile = open(filename, 'w')
    writeFile.write ('Position Data for Tapping Exercise, Total Taps:,' + 
                     str(trials[i]) + '\n' + \
                 'Time (s),' + \
                 'Finger 1,,,' + \
                 'Finger 2,,,' + \
                 'Finger 3,,,' + \
                 'Finger 4,,,' + \
                 'Finger 5\n' + \
                 ',x,y,z,x,y,z,x,y,z,x,y,z,x,y,z\n')
# Write the gathered data to file
    for row in datalog[i]:
        for element in row:
            writeFile.write(str(element) + ',')
        writeFile.write('\n')
    writeFile.close()  
pygame.quit()
 

