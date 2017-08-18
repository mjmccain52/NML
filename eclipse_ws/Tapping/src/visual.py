import pygame, Leap, nml


# Colors assigned by RGB values
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GREEN = (  0, 255,   0)
RED   = (255,   0,   0)

BUFF = 40
STROKE = 5
CURSOR = 15
FONT_SIZE = 20
SCREEN_X = 525
SCREEN_Y = 500

pygame.init()
screen_size = (SCREEN_X,SCREEN_Y)
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("Visual Feedback")
screen.fill(WHITE)

clock = pygame.time.Clock()
controller = Leap.Controller()
while controller.frame().interaction_box.width == 0:
    pass
box = controller.frame().interaction_box
running = True
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
    pygame.draw.rect(screen, RED, (BUFF,BUFF,w,d), STROKE) #Top
    pygame.draw.rect(screen, RED, (BUFF,2*BUFF+d,w,h), STROKE) # Front
    pygame.draw.rect(screen, RED, (2*BUFF+w,2*BUFF+d,d,h), STROKE) # Right

    # Writing text on the screen is suprisingly complex
    font = pygame.font.Font(None, FONT_SIZE)
    text = font.render("Top View", 1, BLACK)
    textpos = text.get_rect()
    textpos.center = (int(BUFF +w/2),int(BUFF/2))
    screen.blit(text, textpos)
    text = font.render("Front View", 1, BLACK)
    textpos = text.get_rect()
    textpos.center = (int(BUFF +w/2),int(3*BUFF/2+d))
    screen.blit(text, textpos)
    text = font.render("Right View", 1, BLACK)
    textpos = text.get_rect()
    textpos.center = (int(2*BUFF+w+d/2),int(3*BUFF/2+d))
    screen.blit(text, textpos)
    if len(frame.hands) == 1:
        hand = frame.hands[0]
        pos = hand.palm_position

        x = pos[0]
        y = pos[1]
        z = pos[2]
        c = box.center
        xc = x - c[0]
        yc = y - c[1]
        zc = z - c[2]

        # Top view (x-z)
        if BUFF+w/2+xc > 0 and BUFF+w/2+xc < SCREEN_X \
           and BUFF+d/2+zc > 0 and BUFF+d/2+zc < SCREEN_Y:
            pygame.draw.circle(screen, BLACK, (int(BUFF+w/2+xc),int(BUFF+d/2+zc)), CURSOR)
        # Front view (x-y)
        if BUFF+w/2+xc > 0 and BUFF+w/2+xc < SCREEN_X \
           and 2*BUFF+d+h/2-yc > 0 and 2*BUFF+d+h/2-yc < SCREEN_Y:
            pygame.draw.circle(screen, BLACK, (int(BUFF+w/2+xc),int(2*BUFF+d+h/2-yc)), CURSOR)

        # Right view (z-y)
        if 2*BUFF+w+d/2-zc > 0 and 2*BUFF+w+d/2-zc < SCREEN_X \
           and 2*BUFF+d+h/2-yc > 0 and 2*BUFF+d+h/2-yc <SCREEN_Y:
            pygame.draw.circle(screen, BLACK, (int(2*BUFF+w+d/2-zc),int(2*BUFF+d+h/2-yc)), CURSOR)
    pygame.display.flip()
        
    clock.tick(50)
pygame.quit()



