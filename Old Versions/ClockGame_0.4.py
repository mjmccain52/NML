################################################################################
#
# Clock Game presents various targets one at a time, alternating between
# the center of the screen and 8 positions around a perimeter of a large 
# circle. As the user positions the mouse over a target, the target will
# "load" for a moment to pause the user's motion, then disappear and another
# target will be presented
#
# Author: Michael McCain
# Date: 4 September 2013
#
################################################################################

import pygame, random, Leap, sys, ctypes
from math import pi, sqrt, isnan

SPACING = 400

def initialize_graphics():
    pygame.init() #Initialize game engine
    # Set up screen
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

# Change these constants to alter general sizes/layout (pixels)


TARGET_SIZE = 50

#Refresh rate of loop in frames per second. Affects how fast targets load
FRAMERATE = 30 

# Colors assigned by RGB values
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GREEN = (  0, 255,   0)
RED   = (255,   0,   0)

class Circle:
    def __init__(self, position, radius=TARGET_SIZE):
        self.position = position
        self.radius = radius
        
    
class ClockLeapListener(Leap.Listener):
    cur_x = 0
    cur_y = 0

    def moveMouse(self, x, y, zf):    
        global screen
        if self.cur_x != x or self.cur_y != y:      
            self.cur_x = x
            self.cur_y = y
            rad = 15 + int(zf)
            if rad <= 0:
                rad = 1
            pygame.draw.circle(screen, RED,(int(x),int(y)), rad)
            pygame.event.post(pygame.event.\
                              Event(pygame.USEREVENT, {'pos':(x,y)}))
            pygame.display.flip()
            
    def on_frame(self, controller):
        frame = controller.frame()
        global screen_x
        global screen_y
        if not frame.fingers.is_empty:
            fingers = frame.fingers
            monitor = controller.located_screens[0]
            normal = monitor.intersect(fingers[0],True)
            if not (isnan(normal[0]) or isnan(normal[1])):
                
                xPoint = screen_x * normal[0]
                yPoint = screen_y * normal[1]
                zFactor = fingers[0].tip_position[2] / -20.0
                self.moveMouse(int(xPoint), int(screen_y - yPoint), zFactor)
        
def isInTarget(position, target):
    """Determine whether the position of the mouse lies within the target
        using Pythagorean Theorem"""
    x, y = position[0], position[1]
    center_x, center_y = target[0], target[1]
    return (x - center_x)**2 + (y - center_y)**2 <= TARGET_SIZE**2

def drawTarget(targetIndex, color=BLACK, radius=TARGET_SIZE, clear=False):
    """Draw the indicated target, default color is black, default radius is
        TARGET_SIZE, by default wipe the screen"""
    global screen
    if clear:
        screen.fill(WHITE)
        pygame.draw.circle(screen, RED, (50,50), 30)
    pygame.draw.circle(screen, color, locations[targetIndex], radius)
    pygame.display.flip() # update screen

def update_screen(target, load=None, cursor=None):
    global screen
    screen.fill(WHITE)
    pygame.draw.circle(screen, RED, (50,50), 30)
    pygame.draw.circle(screen, BLACK, target.position, target.radius)
    if load:
        pygame.draw.circle(screen, GREEN, load.position, load.radius)
    if cursor:
        pygame.draw.circle(screen, RED, cursor.position, cursor.radius)
    pygame.display.flip()
    
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
cursor = None
update_screen(ct)
# Loop until the exit signal is given
while not done:   
    update = False

    # Progresses green loading circle if hovering in a target
    if load_circle and not load_circle.radius >= TARGET_SIZE:
        update = True
        load_circle.radius += TARGET_SIZE / 10 # Loading circle gets bigger by tenths

    # If green circle is fully loaded, draw a new target, alternating between
    # center and perimeter
    elif load_circle and load_circle.radius >= TARGET_SIZE:
        update = True
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
        elif event.type == pygame.USEREVENT or event.type == pygame.MOUSEMOTION:
            # Toggle loading if mouse is in target
            if isInTarget(event.pos, locations[currentTarget]):
                if not load_circle:
                    load_circle = Circle(ct.position,0)

            # Reset loading if mouse leaves target
            elif load_circle:
                load_circle = None
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and isInTarget(event.pos, (50,50)):
            done = True
    if update:
        update_screen(ct, load_circle, cursor)


    clock.tick(FRAMERATE) # Limits framerate of loop
            
pygame.quit() # Be IDLE friendly by formally quitting game engine
