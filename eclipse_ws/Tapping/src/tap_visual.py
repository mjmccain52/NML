import pygame, Leap, nml
from time import clock
from os import path, remove
from pylab import plot, show

DEFAULT_TIMER = 5
DEFAULT_FILENAME = "..\\data\\tapping"

MARGIN = 5
SUCCESSES = 3

# Colors assigned by RGB values
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GREEN = (  0, 255,   0)
RED   = (255,   0,   0)
BLUE  = (  0,   0, 255)

BUFF = 40
STROKE = 5
CURSOR = 15
FONT_SIZE = 20
SCREEN_X = 350
SCREEN_Y = 350
GAP = 50
TOP_LINE = 140
BOT_LINE = TOP_LINE + GAP

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
            
print ""
print "Finger Tapping Data Logger"
print "BYU Neuromechanics Lab 2013\n"
print ""
print "This application will track and log data from a single finger"
print "as you quickly wag it up and down above the sensor for a set"
print "period of time."
print ""

trials =[]
files = []
filename = DEFAULT_FILENAME
timer = DEFAULT_TIMER
# Determine whether to use program defaults or user values
prompt = "Use default file (" + DEFAULT_FILENAME + ".csv) and timer (" + \
         str(DEFAULT_TIMER) + " secs)? (y/n):"
error = "Please press 'Y' or 'N' and then ENTER"
choice = nml.two_choice_input_loop(prompt, "y", "n", error)
if choice == "n":
    print "CSV Filename (exclude .csv extension and file path):",
    filename = "..\\data\\" + raw_input()
    print "Timer:",
    timer_string = raw_input()
    while not nml.is_number(timer_string):
        print "Please enter a valid number."
        print "Timer:",
        timer_string = raw_input()
    timer = float(timer_string)

while len(trials) < SUCCESSES:
    filename = DEFAULT_FILENAME
    # If filename has previously been used, append a number to it
    while path.exists(filename + ".csv"):
        num = ""
        reverse = filename[::-1]
        if reverse[0].isdigit():
            for char in reverse:
                if char.isdigit():
                    num = char + num
                else:
                    break
            new_num = int(num) + 1
            filename = filename[:-1*len(num)] + str(new_num)
        else:
            filename = filename + "1"
    filename += ".csv"
    
    # See if writing to the file results in an error.
    try:
        writeFile = open(filename,'w')
    except:
        print "Couldn't access",filename, "because it is open in another " + \
              "program.\nPlease close",filename, "and try again."
        print "Press ENTER to exit."
        raw_input()
        exit()
    try:
        writeFile = open(filename, 'w')
        writeFile.close()
    except:
        print "IO error.", filename, "most likely open somewhere else."
        exit() # Quit if there's an error    
    
    pygame.init()
    screen_size = (SCREEN_X,SCREEN_Y)
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("Visual Feedback")
    screen.fill(WHITE)
    
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
    while running:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT:
                running = False
        frame = controller.frame()
        box = frame.interaction_box
        w = box.width
        h = box.height
        d = box.depth
        screen.fill(WHITE)
        pygame.draw.rect(screen, RED, (BUFF,BUFF,w,h), STROKE)
        pygame.draw.line(screen, BLACK, (BUFF+w/2-10, BUFF+h/2),(BUFF+w/2+10, BUFF+h/2))
        pygame.draw.line(screen, BLACK, (BUFF+w/2, BUFF+h/2-10),(BUFF+w/2, BUFF+h/2+10))
        pygame.draw.line(screen, BLUE, (BUFF, TOP_LINE),(BUFF+w, TOP_LINE))
        pygame.draw.line(screen, BLUE, (BUFF, BOT_LINE),(BUFF+w, BOT_LINE))
        
        # Writing text on the screen is surprisingly complex
        font = pygame.font.Font(None, FONT_SIZE)
        text = font.render("Trial #"+str(len(trials)+1)+", taps: " + str(counter), 1, BLACK)
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
            xc = x - c[0]
            yc = y - c[1]
            zc = z - c[2]
            # Front view (x-y)
            if BUFF+w/2+xc > 0 and BUFF+w/2+xc < SCREEN_X \
               and BUFF+h/2-yc > 0 and BUFF+h/2-yc < SCREEN_Y:
                pygame.draw.circle(screen, BLACK, (int(BUFF+w/2+xc),int(BUFF+h/2-yc)), CURSOR)
            if first and BUFF+h/2-yc < TOP_LINE:
                first = False
                ready = True
    
            if BUFF+h/2-yc > BOT_LINE and ready:
                ready = False
                start = clock()
                print "Reading data. . ."
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
    
    writeFile = open(filename, 'w')
    writeFile.write ('Position Data for Tapping Exercise\n' + \
                     'Time (s),' + \
                     'Finger 1,,,' + \
                     'Finger 2,,,' + \
                     'Finger 3,,,' + \
                     'Finger 4,,,' + \
                     'Finger 5\n' + \
                     ',x,y,z,x,y,z,x,y,z,x,y,z,x,y,z\n')
    # Write the gathered data to file
    t =[]
    y =[]
    for row in listener.data:
        #t.append(row[0])
        #y.append(row[2])
        for element in row:
            writeFile.write(str(element) + ',')
        writeFile.write('\n')
    writeFile.close()
    
    #plot(t,y)
    #show()
    for trial in trials:
        if abs(counter - trial) > MARGIN:
            trials = []
            for tap_file in files:
                remove(tap_file)
            files = []
    trials.append(counter)
    files.append(filename)
    
pygame.quit()
 

