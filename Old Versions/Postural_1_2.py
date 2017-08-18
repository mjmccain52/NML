"""Postural Tremor Sensor

Author: Michael McCain
Last updated: 2/3/2014

Uses the Leap Motion controller to gather data over time of one hand. Data
is gathered for a specified time period at the refresh rate of the
controller.

Changes from v1_1:
    -GUI-based
    -When position detection is enabled, once the hand is in the interaction
     box, the program will wait one second before starting the timer.   
"""
# Python libraries
from time import clock, strftime
from os import path, makedirs

# 3rd-party libraries
import Leap, pygame
from easygui import msgbox, enterbox, ynbox, buttonbox

# Custom libraries
from colors import WHITE, BLACK

TIMER = 15 # Time interval to collect data in seconds
FILENAME = 'postural'
FOLDER = "..\\data"

FONT_FILENAME = "times.ttf"
FONT_FOLDER = "fonts"
IMG_FOLDER = "img"

# Filenames and relative paths (if necessary) to hand images
GREEN_HAND = "ghand.png"
RED_HAND = "rhand.png"
LOGO = "logo.png"
# Size of hand icons
HAND_SIZE_PX = (40,40) # px X px
# Percent of window that interaction box will occupy
INTERACTION_RATIO = .75
# Font Size
FONT_SIZE_PX = 20
# Timer Font Size
TIMER_FONT_SIZE_PX = 40
# Space between top of window and written text
TEXT_BUFFER_PX = 30
# Window Size
WIN_SIZE_PX = 300
# Refresh rate of graphics window
FRAMERATE = 60 # Hz
class PostureListener(Leap.Listener):
    """Once activated, listens for any Leap input, interrupting any current
    process.
    """
    
    def on_init(self, controller):
        """Runs automatically when PostureListener is initialized. Used here
        to initialize empty data matrix.

        Args:
        controller (Leap.Controller):    Leap controller object that had this
                                         listener instance added to it.
        """
        self.data = [] # Hand Data is stored here until ready to write to file.

    def on_frame(self, controller):
        """ Runs every time the Leap detects interaction, anywhere from 50 to 
        200 frames per second.

        Args:
            controller (Leap.Controller): Leap controller object that had 
                                          this listener instance added to it.
        """
        
        frame = controller.frame() # Grab current frame of Leap data        
        global a_sec_start
        global positioning # If True, initial positioning still not complete.
        global wait_a_sec
        if not button_activated and positioning:
            if len(frame.hands) == 1: # Checks for 1 hand                
                hand1 = frame.hands[0]

                # End initial positioning if hand is clearly visible
                box = frame.interaction_box
                c = box.center
                x_check = abs(c[0]- hand1.palm_position[0]) < box.width / 2.0
                y_check = abs(c[1]- hand1.palm_position[1]) < box.height / 2.0
                z_check = abs(c[2]- hand1.palm_position[2]) < box.depth / 2.0
                if x_check and y_check and z_check:
                    positioning = False
                    wait_a_sec = True
                    a_sec_start = clock()                   
        elif wait_a_sec:
            pass        
        # Once reading data, only record if hand is still visible        
        elif len(frame.hands) > 0:
            currentTime = clock() # Timestamp
            hand = frame.hands[0]     
            position = hand.palm_position

            # XYZ for palm center
            x = position[0] 
            y = position[1] 
            z = position[2] 

            #Vector for the palm normal
            pn = hand.palm_normal           

            # Palm velocity vector
            pv = hand.palm_velocity

            row = [currentTime-start,x,y,z,pn[0],pn[1],pn[2],pv[0],pv[1],pv[2]]
            
            # Loop through all visible fingers, appending their position data
            # to the current row
            for finger in frame.fingers:
                pos = finger.tip_position
                row.extend([pos[0],pos[1],pos[2]])

            self.data.append(row)

def write_text(screen, msg, pos, size):
    """ writes a message in black Times New Roman font to a specified position
    in the graphics window.
    
    Args:
        screen (pygame.Surface): The surface where the text will be written
        msg (str):               The message to be written
        pos (tuple<int>):        The x-y coordinates of the upper left of the
                                 textbox relative to 'screen'
        size (int):              Font size
    """
    # This line of code needs to be in a separate function like this if the 
    # program is looped otherwise it will crash due to some error in pygame
    font = pygame.font.Font(path.join(FONT_FOLDER, FONT_FILENAME), size)
    text = font.render(msg, 1, BLACK)
    textpos = text.get_rect()
    textpos.center = pos
    screen.blit(text, textpos)
    
def main():
    
    msgbox("Postural Tremor Data Logger for One Hand\n"
           "BYU Neuromechanics Research Group 2014\n\n"
           "This application will track and log data from one of your hands "
           "as you hold it in a fixed position above the sensor for " 
           + str(TIMER) + " seconds.")
    name = enterbox("Please enter your last name (no spaces)","Name Entry")
    if name == None:
        name = ""

    # This loop enables multiple data readings
    while True:
        # Stores the date and time as a string, 
        # ex: 20140203111537 = 2/3/2014, 11:15 AM and 37 seconds
        run_timestamp = strftime("%Y%m%d%H%M%S")
        
        # Instuctions
        choice = buttonbox( "You have the option of starting the data logging "
                            "process by pressing a button with the alternate "
                            "hand, or by having the sensor detect that "
                            "your hand is in position automatically.\n\n"
                            "Please choose a method to trigger data logging",
                            "Choose Trigger Method",
                            ("Button","Hand Detection"))
        global button_activated # If True, no initial positioning necessary.
        button_activated = True
        if choice is not "Button":
            button_activated = False
        global start  # Time of initial recording  
        
        # Create a listener and controller
        listener = PostureListener()
        controller = Leap.Controller()
        # Will turn true while initial hand positioning is happening       
        global positioning
        global wait_a_sec 
        positioning = False
        wait_a_sec = False
                
        if button_activated:
            msgbox("Place your hand about 7 inches above the controller with "
                   "fingers extended and spread, then with your opposite hand "
                   "press \'OK\' to begin")
            controller.add_listener(listener)
            start = clock()
        else:
            positioning = True
        
            # Once added, the listener is able to disrupt any process with on_frame
            # method if it detects any data.
            controller.add_listener(listener)
        pygame.init() # Initialize graphics engine
        frame_clock = pygame.time.Clock() # Initialize framerate clock
        # Set primary Surface size
        screen = pygame.display.set_mode((WIN_SIZE_PX,WIN_SIZE_PX))
        pygame.display.set_caption("Postural")
        
        # Load images of green and redHands
        try:
            green_hand = pygame.image.load(
                            path.join(IMG_FOLDER, GREEN_HAND)).convert_alpha()
            green_hand = pygame.transform.scale(green_hand,HAND_SIZE_PX)
        except:
            msgbox("Could not find " + GREEN_HAND + ". Press OK to quit.")
            controller.remove_listener(listener)
            pygame.quit()
            exit()
        try:
                
            red_hand = pygame.image.load(
                             path.join(IMG_FOLDER, RED_HAND)).convert_alpha()
            red_hand = pygame.transform.scale(red_hand,HAND_SIZE_PX)
        except:
            msgbox("Could not find " + RED_HAND + ". Press OK to quit.")
            controller.remove_listener(listener)
            pygame.quit()
            exit()
        try:
            logo = pygame.image.load(path.join(IMG_FOLDER, LOGO)).convert()
        except:
            msgbox("Could not find " + LOGO + ".png. Press OK to quit.")
            controller.remove_listener(listener)
            pygame.quit()
            exit()
        # Main graphics window refresh loop. Refreshes at FRAMERATE specified    
        while True:
            
            for event in pygame.event.get(): 
                if event.type == pygame.QUIT and \
                   ynbox("Are you sure you want to quit?"
                         " No data will be recorded"):
                    controller.remove_listener(listener)
                    pygame.quit()
                    exit()
            screen.fill(WHITE)
            frame = controller.frame()
            # The interaction box is a cube in the air above the Leap where 
            # hand interaction is ideal
            box = frame.interaction_box
            # A factor to scale movements to the window size
            scale_factor = WIN_SIZE_PX*INTERACTION_RATIO/box.width
            # Draw the interaction box
            box_size = (int(WIN_SIZE_PX*INTERACTION_RATIO),
                                int(box.depth*scale_factor))
            gui_interaction_box = pygame.Rect((0, 0), box_size)
            gui_interaction_box.center = (WIN_SIZE_PX/2,WIN_SIZE_PX/2)
            
            
            logo_orig_rect = logo.get_rect()
            logo_scale = gui_interaction_box.width/float(logo_orig_rect.width)
            scaled_logo_size_px = (gui_interaction_box.width, 
                                   int(logo_orig_rect.height*logo_scale)) 
            logo = pygame.transform.scale(logo, scaled_logo_size_px)
            logo_rect = logo.get_rect()
            logo_rect.center = gui_interaction_box.center
            screen.blit(logo, logo_rect)
            pygame.draw.rect(screen, BLACK, gui_interaction_box, 3)
            # Draw the hand if visible
            if len(frame.hands) > 0:
                palm = frame.hands[0].palm_position
                hand_rect = green_hand.get_rect()
                hand_rect.center = (int(palm[0]*scale_factor + 
                                        WIN_SIZE_PX/2), 
                                    int(palm[2]*scale_factor + 
                                        WIN_SIZE_PX/2))
                # Green hand inside the interaction box
                if abs(palm[0]) < box.width/2 and abs(palm[2]) < box.depth/2:                    
                    screen.blit(green_hand, hand_rect)
                # Red hand outside
                else:
                    screen.blit(red_hand, hand_rect)
                    
            if positioning or wait_a_sec:
                write_text(screen,"Positioning",
                           (WIN_SIZE_PX/2,TEXT_BUFFER_PX), FONT_SIZE_PX)
                if wait_a_sec and clock() - a_sec_start > 1:
                    wait_a_sec = False
                    start = clock()
            else:
                # Display the current timer
                write_text(screen,str(int(clock() - start + 1)),
                           (WIN_SIZE_PX/2, TEXT_BUFFER_PX), 
                           TIMER_FONT_SIZE_PX)
                # Quit the loop once the timer completes
                if clock() - start > TIMER:
                    controller.remove_listener(listener)
                    pygame.quit()
                    break
            pygame.display.flip() # Update display
            # Wait to run the loop again until 1/FRAMERATE has elapsed
            frame_clock.tick(FRAMERATE)
            
        # Remove the listener when done
        controller.remove_listener(listener)
        pygame.quit()
        
        if not path.exists(FOLDER):
            makedirs(FOLDER)
        filename = FOLDER + "\\" + FILENAME + "_"+ name + \
                   "_" + run_timestamp + ".csv"
        writeFile = open(filename, 'w')
        # In the .csv, date is recorded in the format MM/DD/YYYY
        date = strftime("%m") + "/" + strftime("%d") + "/" + strftime("%Y")
        
        writeFile.write('Postural Tremor Data for One Hand,Subject:,' + name +
                        ',Date:,'+ date + '\n' + 
                        'Time (s),' + 
                        'Palm position (mm),,,' + 
                        'Palm normal vector,,,' + 
                        'Palm velocity (mm/s),,,' + 
                        'Individual Finger Positions - xyz (Unordered)\n'+ 
                        ',x,y,z,i,j,k,x,y,z,' + 
                        'Finger 1,,,Finger 2,,,Finger 3,,,Finger 4,,,' + 
                        'Finger 5\n')
        # Write the gathered data to file
        data = listener.data
        for row in data:
            for element in row:
                writeFile.write(str(element))
                writeFile.write(',')
            writeFile.write('\n')
        writeFile.close()
        msgbox("Data recorded successfully.")
        if not ynbox("Do you wish to run the program again?"):
            return

# This independent statement should be at the bottom of all Python scripts
# that you wish to have a main().
if __name__ == "__main__":
    main()
