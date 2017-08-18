""" Application that counts the number of times a single finger wags up and
down past defined thresholds using the Leap Motion

Changes from v0_6:
        -No armrest
        -Direct correlation of movements to screen
Author: Michael McCain
Date: 23 Jan 2014
      
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

COUNTDOWN = 3
# Length of time for each trial
TIMER = 10 # seconds
# Default base of filename and save location
FILENAME = "tapping"
FOLDER = "..\\data"
TARGET_FILENAME = "black.png"
IMG_FOLDER = "img"
FONT_FILENAME = "times.ttf"
FONT_FOLDER = "fonts"
# Maximum allowable difference between trials
MARGIN = 5
# Required consecutive successful trials
SUCCESSES = 5

# Cursor Size
CURSOR_PX = 15
# Font Size
FONT_SIZE_PX = 20
# Window Size
WINDOW_SIZE_MM = int(6*25.4)
# Distance required to tap 
GAP_MM = 15 #mm
# Timer Font Size
TIMER_FONT_SIZE_PX = 40
# Space between top of window and written text
TEXT_BUFFER_PX = 30

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
            
def write_text(screen, msg, pos, size, centered=True):
    """ writes a message in black Times New Roman font to a specified position
    in the graphics window.
    
    Args:
        screen (pygame.Surface): The surface where the text will be written
        msg (str):               The message to be written
        pos (tuple<int>):        The x-y coordinates of the textbox relative 
                                 to the top left of 'screen'
        size (int):              Font size
        centered (bool):         Text is centered at pos if True, middle left
                                 of text at pos if False
    """
    font = pygame.font.Font(path.join(FONT_FOLDER, FONT_FILENAME), size)
    text = font.render(msg, 1, BLACK)
    textpos = text.get_rect()
    if centered:
        textpos.center = pos
    else:
        textpos.topleft = pos
    screen.blit(text, textpos)

#
# PROGRAM STARTS RUNNING HERE
#
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
win_size_px = int(WINDOW_SIZE_MM*ppmm)
name = enterbox("Please enter your last name (no spaces)","Name Entry")
if name == None:
    name = ""
TOP_LINE = int(win_size_px/2 - GAP_MM/2*ppmm)
BOT_LINE = int(win_size_px/2 + GAP_MM/2*ppmm)
               
msgbox( "This application will track and log data from a single finger as you"
        " quickly wag it up and down above the sensor for " + str(TIMER)
        + " seconds. There will be a brief countdown for you to move your hand"
        " into position.",
         "Finger Tapping Data Logger")
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

while len(trials) < SUCCESSES:    
    
    frame_clock = pygame.time.Clock()
    controller = Leap.Controller()
    listener = TapListener()
    
    precount = True
    running = True
    counter = 0
    past_down = False
    ready = False
    start = 0
     
    screen = pygame.display.set_mode((win_size_px,win_size_px))
    pygame.display.set_caption("Tapping")
    try:
        cursor = pygame.image.load(path.join(IMG_FOLDER, 
                                        TARGET_FILENAME)).convert_alpha()
    except:
        msgbox("Could not find " + TARGET_FILENAME +". Press OK to quit.") 
        pygame.quit()
        controller.remove_listener(listener)
        exit()                                   
    cursor = pygame.transform.scale(cursor, (CURSOR_PX*2,CURSOR_PX*2))
    screen.fill(WHITE)
    countdown_start = clock()
    while running:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT and \
               ynbox("Are you sure you want to quit?"
                     " No data will be recorded"):
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
        try:
            font = pygame.font.Font(path.join(FONT_FOLDER, FONT_FILENAME), 
                                FONT_SIZE_PX)
        except:
            msgbox("Could not find " + FONT_FILENAME +". Press OK to quit.")
            pygame.quit()
            controller.remove_listener(listener)
            exit()
        write_text(screen,"Trial #" + str(len(all_trials) + 1) + ", taps: " + 
                   str(counter), (TEXT_BUFFER_PX, TEXT_BUFFER_PX), 
                   12, False) 
        if precount:
            timer = clock() - countdown_start
            if timer < COUNTDOWN:
                write_text(screen,str(int(COUNTDOWN - timer + 1)),
                           (win_size_px/2, TEXT_BUFFER_PX), 
                           TIMER_FONT_SIZE_PX)
            elif timer >= COUNTDOWN and timer < COUNTDOWN + 1:
                    write_text(screen,"Begin", 
                               (win_size_px/2, TEXT_BUFFER_PX), 
                               TIMER_FONT_SIZE_PX)
            else:
                precount = False
                start = clock()
                controller.add_listener(listener)
        if len(frame.fingers) > 0:
            finger = frame.fingers[0]
            
            pos = finger.tip_position
            
            xy = cal_data.finger_to_graphics(pos, (win_size_px, win_size_px))
            cx = xy[0] - CURSOR_PX
            cy = xy[1] - CURSOR_PX
            screen.blit(cursor,(cx,cy))
              
            if xy[1] > BOT_LINE and not past_down and not precount:
                past_down = True
                counter +=1
            if xy[1] < TOP_LINE and past_down and not precount:
                past_down = False
        if start > 0 and clock() - start > TIMER:
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
    if high - low > MARGIN:
        msg += " unsuccessfully. Starting over"
        trials = []
        datalog = []
        high = counter
        low = counter
        
    all_trials.append(counter)
    all_data.append(listener.data)
    trials.append(counter)
    datalog.append(listener.data)
    if len(all_trials) == 10 and len(trials) < SUCCESSES:
        datalog = all_data
        trials = all_trials
        break
    msgbox(msg)
    msgbox("Please rest for 90-120 seconds, then press OK to begin next trial.")
my_sum = 0
for c in trials:
    my_sum += c
avg = my_sum/len(trials)

msgbox("Trials completed.\n Average: " + str(avg))
# Create a folder for the data if it's not there
if not path.exists(FOLDER):
    makedirs(FOLDER)
for i in range(len(datalog)):
    filename = FOLDER + "\\" + FILENAME + "_"+ name + "_" + \
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
 

