import pygame, Leap, nml
from time import clock
TIMER = 5

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
SCREEN_X = 400
SCREEN_Y = 400
GAP = 50
TOP_LINE = 140
BOT_LINE = TOP_LINE + GAP

pygame.init()
screen_size = (SCREEN_X,SCREEN_Y)
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("Visual Feedback")
screen.fill(WHITE)

frame_clock = pygame.time.Clock()
controller = Leap.Controller()
while controller.frame().interaction_box.width == 0:
    pass
box = controller.frame().interaction_box
running = True
counter = 0
past_down = False
first = True
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
    
    # Writing text on the screen is suprisingly complex
    font = pygame.font.Font(None, FONT_SIZE)
    text = font.render(str(counter), 1, BLACK)
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
            start = clock()
        if BUFF+h/2-yc > BOT_LINE and not first:
            past_down = True
        if BUFF+h/2-yc < TOP_LINE and past_down:
            past_down = False
            counter +=1
        if start > 0 and clock() - start > TIMER:
            break
            


    pygame.display.flip()
        
    frame_clock.tick(60)
pygame.quit()

print counter

