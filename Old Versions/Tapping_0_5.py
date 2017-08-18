import pygame, Leap, nml
from time import clock, strftime
from os import path, makedirs, environ
from easygui import msgbox, enterbox,ynbox
from colors import BLACK, WHITE, BLUE
import screen_calibration
DEFAULT_TIMER = 10
DEFAULT_FILENAME = "tapping"
DEFAULT_FOLDER = "..\\data"
MARGIN = 5
SUCCESSES = 3

CURSOR = 15
FONT_SIZE = 20
WINDOW_SIZE_MM = int(5*25.4) 
GAP = 15 #mm
TOP_LINE = int(2.3*25.4)


class TapListener(Leap.Listener):
    """Once activated, listens for any Leap input, interrupting any current
    process.
    """

    def on_init(self, controller):
        self.data = []
    def on_frame(self, controller):
        """Runs everytime the Leap detects interaction, anywhere from 50 to 200
        frames per second.

        Keyword arguments:
        controller -- Leap controller object that had this listener instance
                      added to it.
        """
        
        global start # Time of initial recording
        frame = controller.frame() # Grab current frame of Leap data 

        # If hand and fingers are visible, record timestamp and y-position
        # for each finger.
        fingers = frame.fingers
        if not fingers.is_empty:
            frame_data = [clock() - start] # Row to be added to y_data
            frame_data.extend(nml.finger_positions_to_list(fingers))
            self.data.append(frame_data)

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
win_size_px = int(WINDOW_SIZE_MM*ppmm)
name = enterbox("Please enter your last name (no spaces)","Name Entry")
if name == None:
    name = ""
BOT_LINE = int((TOP_LINE+GAP)*ppmm)
TOP_LINE = int(TOP_LINE*ppmm)                
msgbox( "This application will track and log data from a single finger as you quickly wag it up and down above the sensor for a set period of time.", \
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
    
    running = True
    counter = 0
    past_down = False
    first = True
    ready = False
    start = 0
    frame = controller.frame()
    
    screen = pygame.display.set_mode((win_size_px,win_size_px))
    pygame.display.set_caption("Visual Feedback")
    screen.fill(WHITE)
    while running:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT:
                controller.remove_listener(listener)
                pygame.quit()
                exit()
        frame = controller.frame()

        screen.fill(WHITE)
        pygame.draw.line(screen, BLACK, (win_size_px/2-10, win_size_px/2),(win_size_px/2+10, win_size_px/2))
        pygame.draw.line(screen, BLACK, (win_size_px/2, win_size_px/2-10),(win_size_px/2, win_size_px/2+10))
        pygame.draw.line(screen, BLUE, (0, TOP_LINE),(win_size_px, TOP_LINE))
        pygame.draw.line(screen, BLUE, (0, BOT_LINE),(win_size_px, BOT_LINE))
        
        # Writing text on the screen is surprisingly complex
        font = pygame.font.Font(None, FONT_SIZE)
        text = font.render("Trial #"+str(len(all_trials)+1)+", taps: " + str(counter), 1, BLACK)
        textpos = text.get_rect()
        textpos.center = (win_size_px/2,20)
        screen.blit(text, textpos)
        if len(frame.fingers) > 0:
            finger = frame.fingers[0]
            
            pos = finger.tip_position
            xy = cal_data.finger_to_graphics(pos, (win_size_px, win_size_px))
            pygame.draw.circle(screen, BLACK, xy, CURSOR)
            if first and xy[1] < TOP_LINE:
                first = False
                ready = True
     
            if xy[1] > BOT_LINE and ready:
                ready = False
                start = clock()
                controller.add_listener(listener)
                
                
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
my_sum = 0
for c in trials:
    my_sum += c
avg = my_sum/len(trials)

msgbox("Trials completed.\n Average: " + str(avg))
# Create a folder for the data if it's not there
if not path.exists(DEFAULT_FOLDER):
    makedirs(DEFAULT_FOLDER)
for i in range(len(datalog)):
    filename = DEFAULT_FOLDER + "\\" + DEFAULT_FILENAME + "_"+ name + "_" + run_timestamp + "_"+str(i)+".csv"
    writeFile = open(filename, 'w')
    writeFile.write ('Position Data for Tapping Exercise, Total Taps:,' + str(trials[i]) + '\n' + \
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
 

