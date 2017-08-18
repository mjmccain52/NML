import pygame, Leap, nml
from time import clock, strftime
from os import path, makedirs
from pylab import plot, show
from easygui import msgbox, enterbox
from colors import BLACK, WHITE, GREEN, RED, BLUE
DEFAULT_TIMER = 10
DEFAULT_FILENAME = "tapping"
DEFAULT_FOLDER = "..\\data"
PPMM = 3.7
MARGIN = 5
SUCCESSES = 3

BUFF = 40
STROKE = 5
CURSOR = 15
FONT_SIZE = 20
SCREEN_X = 350
SCREEN_Y = 350
GAP = 15 #mm
TOP_LINE = 400
BOT_LINE = TOP_LINE + int(GAP*PPMM)

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

name = enterbox("Please enter your last name (no spaces)","Name Entry")
if name == None:
    name = ""
                
msgbox( "This application will track and log data from a single finger as you quickly wag it up and down above the sensor for a set period of time.", \
         "Finger Tapping Data Logger")
all_trials = []
all_data = []
trials =[]
datalog = []
high = None
low = None
# Determine whether to use program defaults or user values
pygame.init()
run_timestamp = strftime("%Y%m%d%H%M%S")
while len(trials) < SUCCESSES:    
    
    frame_clock = pygame.time.Clock()
    controller = Leap.Controller()
    listener = TapListener()
    
    while controller.frame().interaction_box.width == 0:
        pass
    box = controller.frame().interaction_box
    running = True
    counter = 0
    past_down = False
    first = True
    ready = False
    start = 0
    frame = controller.frame()
    box = frame.interaction_box
    w = box.width * PPMM
    h = box.height * PPMM
    
    screen_size = (int(w+2*BUFF),int(h+2*BUFF))
    screen = pygame.display.set_mode(screen_size)
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
        pygame.draw.rect(screen, RED, (BUFF,BUFF,w,h), STROKE)
        pygame.draw.line(screen, BLACK, (BUFF+w/2-10, BUFF+h/2),(BUFF+w/2+10, BUFF+h/2))
        pygame.draw.line(screen, BLACK, (BUFF+w/2, BUFF+h/2-10),(BUFF+w/2, BUFF+h/2+10))
        pygame.draw.line(screen, BLUE, (BUFF, TOP_LINE),(BUFF+w, TOP_LINE))
        pygame.draw.line(screen, BLUE, (BUFF, BOT_LINE),(BUFF+w, BOT_LINE))
        
        # Writing text on the screen is surprisingly complex
        font = pygame.font.Font(None, FONT_SIZE)
        text = font.render("Trial #"+str(len(all_trials)+1)+", taps: " + str(counter), 1, BLACK)
        textpos = text.get_rect()
        textpos.center = (int(BUFF +w/2),int(BUFF/2))
        screen.blit(text, textpos)
        if len(frame.fingers) > 0:
            finger = frame.fingers[0]
            pos = finger.tip_position
    
            x = pos[0]
            y = pos[1]
            z = pos[2]
            c = box.center
            xc = (x - c[0]) * PPMM
            yc = (y - c[1]) * PPMM
            zc = (z - c[2]) * PPMM
            # Front view (x-y)
            pygame.draw.circle(screen, BLACK, (int(BUFF+w/2+xc),int(BUFF+h/2-yc)), CURSOR)
            if first and BUFF+h/2-yc < TOP_LINE:
                first = False
                ready = True
    
            if BUFF+h/2-yc > BOT_LINE and ready:
                ready = False
                start = clock()
                #print "Reading data. . ."
                controller.add_listener(listener)
            if BUFF+h/2-yc > BOT_LINE and not first and not past_down:
                past_down = True
                counter +=1
            if BUFF+h/2-yc < TOP_LINE and past_down:
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
    if len(all_trials) == 10 and len(trials) == 1:
        datalog = all_data
        trials = all_trials
        break
        


    msgbox(msg)
my_sum = 0
for c in trials:
    my_sum += c
avg = my_sum/len(trials)
# If filename has previously been used, append a number to it
msgbox("Trials completed.\n Average: " + str(avg))
    # Create a folder for the data if it's not there
if not path.exists(DEFAULT_FOLDER):
    makedirs(DEFAULT_FOLDER)
for i in range(len(datalog)):
    filename = DEFAULT_FOLDER + "\\" + DEFAULT_FILENAME + "_"+ name + "_" + run_timestamp + ".csv"
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
 

