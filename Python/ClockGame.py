################################################################################
#
# Clock Game presents various targets one at a time, alternating between
# the center of the screen and 8 positions around a perimeter of a large 
# circle. As the user positions the mouse over a target, the target will
# "load" for a moment to pause the user's motion, then disappear and another
# target will be presented
#
# Author: Michael McCain
# Date: 4 June 2013
#
################################################################################

import pygame, random, Leap, sys, ctypes
from math import pi, sqrt, isnan

# Get the monitor dimensions for fullscreen and Leap pointing
user32 = ctypes.windll.user32
SCREEN_X = user32.GetSystemMetrics(0)
SCREEN_Y = user32.GetSystemMetrics(1)

# Change these constants to alter general sizes/layout (pixels)
SCREEN_SIZE = (SCREEN_X,SCREEN_Y)
SPACING = 400
TARGET_SIZE = 50

#Refresh rate of loop in frames per second. Affects how fast targets load
FRAMERATE = 30 

# Colors assigned by RGB values
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GREEN = (  0, 255,   0)
RED   = (255,   0,   0)

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
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'pos':(x,y)}))
            pygame.display.flip()
            
    def on_frame(self, controller):
        frame = controller.frame()

        if not frame.fingers.empty:
            fingers = frame.fingers
            screen = controller.located_screens[0]
            normal = screen.intersect(fingers[0],True)
            xPoint = SCREEN_X * normal[0]
            yPoint = SCREEN_Y * normal[1]
            zFactor = fingers[0].tip_position[2] / -20.0
            if not (isnan(xPoint) or isnan(yPoint)):
                self.moveMouse(int(xPoint), int(SCREEN_Y - yPoint), zFactor)
        
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
    
pygame.init() #Initialize game engine
listener = ClockLeapListener()
controller = Leap.Controller()
controller.add_listener(listener)

# Set up screen
pygame.display.set_caption("Clock Game")
global screen
if SCREEN_SIZE[0] == SCREEN_X:
    fullscreen = pygame.FULLSCREEN
else:
    fullscreen = 0 
screen = pygame.display.set_mode(SCREEN_SIZE,fullscreen)

clock = pygame.time.Clock() # clock is used to control framerate in the loop

random.seed() # Initialize random number generator

# Determine distances based on screen size and spacing
diag = int(sqrt(1/2.0*SPACING**2))
centerx = SCREEN_SIZE[0] / 2
centery = SCREEN_SIZE[1] / 2

# Target locations start at center, then north and proceed clockwise
locations = [(centerx, centery),\
             (centerx, centery - SPACING), (centerx + diag, centery - diag),\
             (centerx + SPACING, centery), (centerx + diag, centery + diag),\
             (centerx, centery + SPACING), (centerx - diag, centery + diag),\
             (centerx - SPACING, centery), (centerx - diag, centery - diag)]
			 
# Various flag/progress values
backToCenter = True
loading = False
loaded = False
loadingRadius = 0
done = False

# Draw first target in the center of the screen
currentTarget = 0
drawTarget(currentTarget, clear=True)
# Loop until the exit signal is given
while not done:   
    

    # Progresses green loading circle if hovering in a target
    if loading and not loaded:
        loadingRadius += TARGET_SIZE / 10 # Loading circle gets bigger by tenths
        drawTarget(currentTarget, GREEN, loadingRadius)
        if loadingRadius >= TARGET_SIZE:
            loaded = True
            loading = False

    # If green circle is fully loaded, draw a new target, alternating between
    # center and perimeter
    elif loaded:
        if backToCenter:
            # Randomly choose one of the perimeter targets
            currentTarget = random.randrange(1,len(locations)) 
            backToCenter = False
        else:
            currentTarget = 0
            backToCenter = True
            
        drawTarget(currentTarget, clear=True)
        loaded = False
        loadingRadius = 0

    # Cycles through list of user actions (mouse motion, clicks, etc.) per frame   
    for event in pygame.event.get(): 
        # User sends shutdown signal
        if event.type == pygame.QUIT:
            done = True

        # Mouse is moving or finger is in Leap range (Custom-defined USEREVENT above)
        elif event.type == pygame.MOUSEMOTION or event.type == pygame.USEREVENT:
            # Toggle loading if mouse is in target
            if isInTarget(event.pos, locations[currentTarget]):
                loading = True

            # Reset loading if mouse leaves target
            elif loading:
                loading = False
                loadingRadius = 0
                drawTarget(currentTarget)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and isInTarget(event.pos, (50,50)):
            done = True
            
    clock.tick(FRAMERATE) # Limits framerate of loop
            
pygame.quit() # Be IDLE friendly by formally quitting game engine
