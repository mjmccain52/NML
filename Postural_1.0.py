"""Postural Tremor Sensor

Author: Michael McCain
Last updated: 9/6/2013

Uses the Leap Motion controller to gather data over time of both hands. Data
is gathered for a specified time period at the refresh rate of the
controller.
"""

import Leap, nml
from time import clock
from os import system, path

DEFAULT_TIMER = 15 # Time interval to collect data in seconds
DEFAULT_FILENAME = 'postural_data'
 
class PostureListener(Leap.Listener):
    """Once activated, listens for any Leap input, interrupting any current
    process.
    """
    
    data = [] # Hand Data is stored here until ready to write to file.

    def on_frame(self, controller):
        """Runs everytime the Leap detects interaction, anywhere from 50 to 200
        frames per second.

        Keyword arguments:
        controller -- Leap controller object that had this listener instance
                      added to it.
        """
        
        frame = controller.frame() # Grab current frame of Leap data        

        global positioning # If True, initial positioning still not complete.
        global keyboard_activated # If True, no initial positioning necessary.
        if not keyboard_activated and positioning:
            if len(frame.hands) == 2: # Checks for 2 hands                
                hand1 = frame.hands[0]
                hand2 = frame.hands[1]

                # End initial positioning if both hands are clearly visible
                if nml.is_in_interaction_box(frame, hand1.palm_position) and \
                   nml.is_in_interaction_box(frame, hand2.palm_position):
                    positioning = False                   
                
        # Once reading data, only record if both hands are visible        
        elif len(frame.hands) == 2:
            # Differentiate left from right hands
            if frame.hands[0].palm_position[0] < \
               frame.hands[1].palm_position[0]:
                left = frame.hands[0]
                right = frame.hands[1]
            else:
                left = frame.hands[1]
                right = frame.hands[0] 

            currentTime = clock() # Timestamp
                
            left_position = left.palm_position
            right_position = right.palm_position

            # XYZ for both palm centers
            xL = left_position[0] 
            yL = left_position[1] 
            zL = left_position[2] 
            xR = right_position[0]
            yR = right_position[1] 
            zR = right_position[2]

            #Vectors for the palm normals
            lpn = left.palm_normal
            rpn = right.palm_normal            

            # Palm velocity vectors
            lpv =left.palm_velocity
            rpv = right.palm_velocity

            global start # Time of initial recording
            global writeFile
            row = [currentTime-start,xL,yL,zL,xR,yR,zR, \
                              lpn[0],lpn[1],lpn[2],rpn[0],rpn[1],rpn[2], \
                              lpv[0],lpv[1],lpv[2],rpv[0],rpv[1],rpv[2]]
            
            # Loop through all visible fingers, appending their position data
            # to the current row
            for finger in frame.fingers:
                pos = finger.tip_position
                row.extend([pos[0],pos[1],pos[2]])

            self.data.append(row)

def main():
    print ""
    print "Postural Tremor Data Logger for Two Hands"
    print "BYU Neuromechanics Lab 2013"
    print ""
    print "This application will track and log data from both of your hands"
    print "as you hold them in a fixed position above the sensor for a set"
    print "period of time."
    print ""

    

    while True:
        filename = DEFAULT_FILENAME
        timer = DEFAULT_TIMER
        # Determine whether to use program defaults or user values
        prompt = "Use default file (" + DEFAULT_FILENAME + ".csv) and timer (" + \
                 str(DEFAULT_TIMER) + " secs)? (y/n):"
        error = "Please press 'Y' or 'N' and then ENTER"
        choice = nml.two_choice_input_loop(prompt, "y", "n", error)
        if choice == "n":
            print "CSV Filename (exclude .csv extension):",
            filename = raw_input()
            print "Timer:",
            timer_string = raw_input()
            while not nml.is_number(timer_string):
                print "Please enter a valid number."
                print "Timer:",
                timer_string = raw_input()
            timer = float(timer_string)
                        
        global writeFile
        # See if writing to the file results in an error.

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
        try:
            writeFile = open(filename,'w')
        except:
            print "Couldn't access",filename, "because it is open in another " + \
                  "program.\nPlease close",filename, "and try again."
            print "Press ENTER to exit."
            raw_input()
            return
        print ""
        print "You have the option of starting the data logging process by"
        print "having an assistant press enter on the keyboard, or by having"
        print "the sensor detect that your hands are in position automatically."
        print ""
        global keyboard_activated # If True, no initial positioning necessary.
        keyboard_activated = True
        prompt = "Please choose a method to trigger data logging:\n" + \
                 "(K)eyboard or (H)and positioning"
        if nml.two_choice_input_loop(prompt, "k", "h") == "h":
            keyboard_activated = False
            
        global start  # Time of initial recording  
        writeFile.write('Postural Tremor Data for Two Hands\n' + \
                        'Time (s),' + \
                        'Left palm position (mm),,,' + \
                        'Right palm position (mm),,,' + \
                        'Left palm normal vector,,,' + \
                        'Right palm normal vector,,,' + \
                        'Left palm velocity (mm/s),,,' + \
                        'Right palm velocity (mm/s),,,'+ \
                        'Individual Finger Positions - xyz (Unordered)\n'+ \
                        ',x,y,z,x,y,z,i,j,k,i,j,k,x,y,z,x,y,z,' + \
                        'Finger 1,,,Finger 2,,,Finger 3,,,Finger 4,,,' + \
                        'Finger 5,,,Finger 6,,,Finger 7,,,Finger 8,,,' + \
                        'Finger 9,,,Finger 10\n')
        
        # Create a listener and controller
        listener = PostureListener()
        controller = Leap.Controller()

        height = nml.interaction_height(controller, False)
        print ""
        print "Place your hands about " + str(height) + " inches above the"
        print "controller with fingers extended and thumbs nearly touching."
        if keyboard_activated:
            print "Assistant may press Enter to begin"
            raw_input()
            controller.add_listener(listener)
        
        else:
            global positioning # If True, initial positioning still not complete.
            positioning = True

            # Once added, the listener is able to disrupt any process with on_frame
            # method if it detects any data.
            controller.add_listener(listener) 

            # Loop indefinitely until hands are in position.
            while positioning:
                pass
        start = clock() # Start the clock to reference all measurements.
        print "Reading hand data. . ."
        
        # This empty loop runs until the time runs out. The listener's on_frame
        # method will execute every time the Leap senses an input.
        while clock() - start < timer:
            pass
            
        # Remove the listener when done
        controller.remove_listener(listener)

        # Write the gathered data to file
        data = listener.data
        for row in data:
            for element in row:
                writeFile.write(str(element))
                writeFile.write(',')
            writeFile.write('\n')
        writeFile.close()
        print ""
        prompt = "Open " + filename + " to view results? (y/n):"
        error = "Please press 'Y' or 'N' and then ENTER"
        if nml.two_choice_input_loop(prompt, "y", "n", error) == "y":
            system("start "+filename)
        prompt = "Run the program again? (y/n):"
        error = "Please press 'Y' or 'N' and then ENTER"
        if nml.two_choice_input_loop(prompt, "y", "n", error) == "n":
            return
        else:
            print "Remembmer to choose a new filename if you wish to keep"
            print "previous data."

# This independent statement should be at the bottom of all Python scripts
# that you wish to have a main().
if __name__ == "__main__":
    main()
