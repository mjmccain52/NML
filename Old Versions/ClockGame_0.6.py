"""Clock Game presents various targets one at a time, alternating between
the center of the screen and 8 positions around a perimeter of a large 
circle. As the user points to a target, the target will "load" for a moment to
pause the user's motion, then disappear and another target will be presented.
Clicking the upper-left red button exits the program.

Author: Michael McCain
Date: 9 September 2013
"""
import pygame, random, Leap, sys, ctypes, nml
from math import pi, sqrt, isnan
from os import system 

# Radius of the Clock Game in pixels (distance from center to perimeter targets)
SPACING = 400
# Size of targets in pixels
TARGET_SIZE = 50
#Refresh rate of loop in frames per second. Affects smoothness of graphics
FRAMERATE = 60
# Time to load a target, in seconds. If you use a fraction, be sure to express
# it as a float, e.g. 1/3.0 or 1.0/3 not 1/3
TARGET_LOAD_TIME = .4                     
# Colors assigned by RGB values
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GREEN = (  0, 255,   0)
RED   = (255,   0,   0)

data = []
class Circle:
    """Simple object to store position and radius
    """
    def __init__(self, position, radius=TARGET_SIZE):
        """Sets up Circle with initial values.

            Keyword arguments:
            position -- 2-dimensional integer tuple with coordinates for the
                        center of the circle (x,y).
            radius (optional) -- integer value for the radius of the circle.
        """
        self.position = position
        self.radius = radius
        
    
class ClockLeapListener(Leap.Listener):
    """ An activated instance of ClockLeapListener will be able to interrupt
    any process in progress to run its own if it sense input.
    """
    cur_x = 0
    cur_y = 0

    def moveMouse(self, x, y, zf):
        """Updates the cursor position and size

        Keyword arguments:
        x -- horizontal position, in pixels, from left of graphics window
        y -- vertical position, in pixels, from top of graphics window
        zf -- depth factor to determine how big the cursor is
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
            pygame.event.post(pygame.event.\
                              Event(pygame.USEREVENT, {'pos':(x,y)}))
            
    def on_frame(self, controller):
        """Runs everytime the Leap detects interaction, anywhere from 50 to 200
        frames per second.

        Keyword arguments:
        controller -- Leap controller object that had this listener instance
                      added to it.
        """
        frame = controller.frame()
        global screen_x
        global screen_y
        global cursor
        if not frame.fingers.is_empty:
            fingers = frame.fingers
            frame_data = nml.finger_positions_to_list(fingers)
            data.append(frame_data)
            monitor = controller.located_screens[0]
            normal = monitor.intersect(fingers[0],True)
            if normal and not (isnan(normal[0]) or isnan(normal[1])):
                
                xPoint = screen_x * normal[0]
                yPoint = screen_y * normal[1]
                zFactor = fingers[0].tip_position[2] / -20.0
                self.moveMouse(int(xPoint), int(screen_y - yPoint), zFactor)
            else:
                cursor = None
        
def initialize_graphics():
    """Set up the game screen, which gets WINDOWS system data for fullscreen.
    Determine based on the screen resolution where the targets will be located.
    """
    pygame.init() #Initialize game engine
    global screen
    global screen_x
    global screen_y
    global locations
    
    # Get the monitor dimensions for fullscreen and Leap pointing
    user32 = ctypes.windll.user32
    screen_x = user32.GetSystemMetrics(0)
    screen_y = user32.GetSystemMetrics(1)
    screen_size = (screen_x,screen_y)
    screen = pygame.display.set_mode(screen_size,pygame.FULLSCREEN)
    pygame.display.set_caption("Clock Game")

    # Determine distances based on screen size and spacing
    diag = int(sqrt(1/2.0*SPACING**2))
    centerx = screen_x / 2
    centery = screen_y / 2
    
    # Target locations start at center, then north and proceed clockwise
    locations = [(centerx, centery),\
             (centerx, centery - SPACING), (centerx + diag, centery - diag),\
             (centerx + SPACING, centery), (centerx + diag, centery + diag),\
             (centerx, centery + SPACING), (centerx - diag, centery + diag),\
             (centerx - SPACING, centery), (centerx - diag, centery - diag)]

def isInTarget(position, target):
    """Determine whether the position of the mouse lies within the target
    using Pythagorean Theorem

    Keyword arguments:
    position -- interger tuple containing position of cursor (x,y)
    target -- interger tuple containing position of current target (x,y)
    """
    x, y = position[0], position[1]
    center_x, center_y = target[0], target[1]
    return (x - center_x)**2 + (y - center_y)**2 <= TARGET_SIZE**2

def update_screen(target, load=None, cursor=None):
    """Redraw the screen with the new locations of targets, cursor, etc.

    Keyword arguments:
    target -- Circle object representing current target
    load -- Circle object representing green loading circle in target
    cursor -- Circle object representing the cursor
    """
    global screen
    screen.fill(WHITE)
    pygame.draw.circle(screen, RED, (50,50), 30)
    pygame.draw.circle(screen, BLACK, target.position, target.radius)
    if load:
        pygame.draw.circle(screen, GREEN, load.position, load.radius)
    if cursor:
        pygame.draw.circle(screen, RED, cursor.position, cursor.radius)
    pygame.display.flip()
print ""
print "Clock Game Data Logger"
print "BYU Neuromechanics Lab 2013"
print ""
print "This application will track and log data from a single finger."
print "Use a single index finger to point at the screen. A red cursor will"
print "track the motion. Black targets will be displayed, appearing in random"
print "order around a central target. Move your hand to point at the current"
print "target. Pause for a moment in the target for the green loading circle to"
print "complete, then proceed to the next target. Use the mouse to click the"
print "circle in the upper-left corner to exit."
print ""

while True:
    filename = "clock.csv"
    prompt = "Use default file (" + filename + ")? (y/n):"
    error = "Please press 'Y' or 'N' and then ENTER"
    choice = nml.two_choice_input_loop(prompt, "y", "n", error)
    if choice == "n":
        print "CSV Filename (exclude .csv extension):",
        filename = raw_input() + ".csv"                
        # See if writing to the file results in an error.
        try:
            testfile = open(filename,'w')
            testfile.close()
        except:
            print "Couldn't access",filename, "because it is open in another " + \
                    "program.\nPlease close",filename, "and try again."
            print "Press ENTER to exit."
            raw_input()
            break
    print "Press Enter to Begin"
    raw_input()
    initialize_graphics()
    listener = ClockLeapListener()
    controller = Leap.Controller()
    controller.add_listener(listener)




    clock = pygame.time.Clock() # clock is used to control framerate in the loop

    random.seed() # Initialize random number generator


                             
    # Various flag/progress values
    backToCenter = True
    done = False

    # Draw first target in the center of the screen
    currentTarget = 0
    #drawTarget(currentTarget, clear=True)
    ct = Circle(locations[0])
    load_circle = None
    global cursor
    cursor = None
    update_screen(ct)
    increment = 0
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

        # If green circle is fully loaded, draw a new target, alternating between
        # center and perimeter
        elif load_circle and load_circle.radius >= TARGET_SIZE:
            update = True
            increment = 0
            load_circle = None
            if backToCenter:
                # Randomly choose one of the perimeter targets
                currentTarget = random.randrange(1,len(locations))
                backToCenter = False
            else:
                currentTarget = 0
                backToCenter = True
                
            ct.position = locations[currentTarget]

        # Cycles through list of user actions (mouse motion, clicks, etc.) per frame   
        for event in pygame.event.get(): 
            # User sends shutdown signal
            if event.type == pygame.QUIT:
                done = True

            # Mouse is moving or finger is in Leap range (Custom-defined USEREVENT
            # above)
            elif event.type == pygame.USEREVENT:
                update = True
                # Toggle loading if mouse is in target
                if isInTarget(event.pos, locations[currentTarget]):
                    if not load_circle:
                        load_circle = Circle(ct.position,0)

                # Reset loading if mouse leaves target
                elif load_circle:
                    increment = 0
                    load_circle = None
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and isInTarget(event.pos, (50,50)):
                done = True
        if update:
            update_screen(ct, load_circle, cursor)


        clock.tick(FRAMERATE) # Limits framerate of loop

    controller.remove_listener(listener)
    pygame.quit()
    
    writeFile = open(filename, 'w')
    writeFile.write ('Position Data for Clock Game\n' + \
                     'Finger 1,,,' + \
                     'Finger 2,,,' + \
                     'Finger 3,,,' + \
                     'Finger 4,,,' + \
                     'Finger 5\n' + \
                     ',x,y,z,x,y,z,x,y,z,x,y,z,x,y,z\n')
    # Write the gathered data to file
    for row in data:
        for element in row:
            writeFile.write(str(element) + ',')
        writeFile.write('\n')
    writeFile.close()
    prompt = "Open " + filename + " to view results? (y/n):"
    error = "Please press 'Y' or 'N' and then ENTER"
    if nml.two_choice_input_loop(prompt, "y", "n", error) == "y":
        system("start "+filename)
    prompt = "Run the program again? (y/n):"
    error = "Please press 'Y' or 'N' and then ENTER"
    if nml.two_choice_input_loop(prompt, "y", "n", error) == "n":
        break
    else:
        print "Remembmer to choose a new filename if you wish to keep"
        print "previous data."
# Be IDLE friendly by formally quitting game engine
