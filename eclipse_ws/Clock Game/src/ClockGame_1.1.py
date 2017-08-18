"""Clock Game presents various targets one at a time, alternating between
the center of the screen and 8 positions around a perimeter of a large 
circle. As the user points to a target, the target will "load" for a moment to
pause the user's motion, then disappear and another target will be presented.
Clicking the upper-left red button exits the program.

Author: Michael McCain
Date: 9 October 2013
"""
import pygame, random, Leap, sys, ctypes, nml
from math import pi, sqrt, isnan
from os import system, path
from time import strftime

HITS = 1
DEFAULT_FILENAME = "..\\data\\clock"
CREATE_PATH = True
# Radius of the Clock Game in pixels (distance from center to perimeter targets)
DIST_FROM_EDGE = 100
# Size of targets in pixels
TARGET_SIZE = 50
#Refresh rate of loop in frames per second. Affects smoothness of graphics
FRAMERATE = 60
# Time to load a target, in seconds. If you use a fraction, be sure to express
# it as a float, e.g. 1/3.0 or 1.0/3 not 1/3
TARGET_LOAD_TIME = 0.2
# Time for Mouse to disappear after movement
MOUSE_TIMER = 3
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


    def on_init(self, controller):
        self.cur_x = 0
        self.cur_y = 0
        self.first = True
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
    
    # Target locations start at center, then north and proceed clockwise
    locations = [(DIST_FROM_EDGE, DIST_FROM_EDGE), (screen_x - DIST_FROM_EDGE, DIST_FROM_EDGE), \
             (DIST_FROM_EDGE, screen_y - DIST_FROM_EDGE), (screen_x - DIST_FROM_EDGE, screen_y - DIST_FROM_EDGE)]

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
    pygame.draw.circle(screen, BLACK, target.position, target.radius)
    if load:
        pygame.draw.circle(screen, GREEN, load.position, load.radius)
    if cursor:
        pygame.draw.circle(screen, RED, cursor.position, cursor.radius)
    pygame.display.flip()

def log_path(current, new):
    if current == 0 and new == 1:
        paths['NW-NE'] += 1
    elif current == 1 and new == 0:
        paths['NE-NW'] += 1
    elif current == 2 and new == 3:
        paths['SW-SE'] += 1
    elif current == 3 and new == 2:
        paths['SE-SW'] += 1
    elif current == 0 and new == 2:
        paths['NW-SW'] += 1
    elif current == 2 and new == 0:
        paths['SW-NW'] += 1
    elif current == 1 and new == 3:
        paths['NE-SE'] += 1
    elif current == 3 and new == 1:
        paths['SE-NE'] += 1
    elif current == 0 and new == 3:
        paths['NW-SE'] += 1
    elif current == 3 and new == 0:
        paths['SE-NW'] += 1
    elif current == 1 and new == 2:
        paths['NE-SW'] += 1
    elif current == 2 and new == 1:
        paths['SW-NE'] += 1
        
def find_path(current, new):
    if current == 0 and new == 1:
        return'NW-NE'
    elif current == 1 and new == 0:
        return 'NE-NW'
    elif current == 2 and new == 3:
        return 'SW-SE'
    elif current == 3 and new == 2:
        return 'SE-SW'
    elif current == 0 and new == 2:
        return 'NW-SW'
    elif current == 2 and new == 0:
        return 'SW-NW'
    elif current == 1 and new == 3:
        return 'NE-SE'
    elif current == 3 and new == 1:
        return 'SE-NE'
    elif current == 0 and new == 3:
        return 'NW-SE'
    elif current == 3 and new == 0:
        return 'SE-NW'
    elif current == 1 and new == 2:
        return 'NE-SW'
    elif current == 2 and new == 1:
        return 'SW-NE'
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
    run_timestamp = strftime("%Y%m%d%H%M%S")
    global paths
    paths = {'NW-NE':0,'NE-NW':0,'SW-SE':0,'SE-SW':0,'NW-SW':0,'SW-NW':0,'NE-SE':0,'SE-NE':0,\
             'NW-SE':0,'SE-NW':0,'NE-SW':0,'SW-NE':0,}

    data = []
    
    print "Press Enter to Begin"
    raw_input()
    initialize_graphics()
    listener = ClockLeapListener()
    controller = Leap.Controller()
    controller.add_listener(listener)
    mouse_frames = int (FRAMERATE * MOUSE_TIMER)
    mouse_frames_count = 0
    pygame.mouse.set_visible(False)
    mouse_on = False
    motion_bug = True

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
    last_one = False
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
            if last_one:
                break
            update = True
            increment = 0
            load_circle = None
            temp = currentTarget
            while temp == currentTarget:
                temp = random.randrange(0,len(locations))
            log_path(currentTarget, temp)
            #paths[find_path(currentTarget, temp)] += 1
        
            last_one = True
            for path in paths:
                if paths[path] < HITS:
                    last_one = False
                    break
            currentTarget = temp        
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
            if event.type == pygame.MOUSEMOTION:
                if not motion_bug:
                    pygame.mouse.set_visible(True)
                    mouse_on = True
                    mouse_frames_count = 0
                else:
                    motion_bug = False
        if update:
            update_screen(ct, load_circle, cursor)

        if mouse_on:
            mouse_frames_count += 1
            if mouse_frames_count >= mouse_frames:
                pygame.mouse.set_visible(False)
                motion_bug = True
                mouse_on = False
                mouse_frames_count = 0

        clock.tick(FRAMERATE) # Limits framerate of loop

    controller.remove_listener(listener)
    pygame.quit() # Be IDLE friendly by formally quitting game engine
    
    filename = DEFAULT_FILENAME + "_"+ run_timestamp + ".csv"
    writeFile = open(filename, 'w')
    writeFile.write ('Time (ms),Position Data for Clock Game(mm)\n' + \
                     ',x,y,z\n')
    # Write the gathered data to file
    for row in data:
        for element in row:
            writeFile.write(str(element) + ',')
        writeFile.write('\n')
    writeFile.close()
    prompt = "Run the program again? (y/n):"
    error = "Please press 'Y' or 'N' and then ENTER"
    if nml.two_choice_input_loop(prompt, "y", "n", error) == "n":
        break

