"""Finger Oscillation Test

Author: Michael McCain
Last updated: 9/6/2013

Uses the Leap Motion controller to gather data from user tapping finger and
thumb together rapidly.
"""

import Leap, nml
from time import clock
from os import system

data = [] # finger postion data is stored here until ready to write to file.
DEFAULT_TIMER = 10
DEFAULT_FILENAME = "tapping.csv"

class TapListener(Leap.Listener):
    """Once activated, listens for any Leap input, interrupting any current
    process.
    """

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
            data.append(frame_data)

def main():
    print ""
    print "Finger Tapping Data Logger"
    print "BYU Neuromechanics Lab 2013\n"
    print ""
    print "This application will track and log data from a single finger"
    print "as you quickly wag it up and down above the sensor for a set"
    print "period of time."
    print ""

    filename = DEFAULT_FILENAME
    timer = DEFAULT_TIMER
    while True:
        # Determine whether to use program defaults or user values
        prompt = "Use default file (" + DEFAULT_FILENAME + ") and timer (" + \
                 str(DEFAULT_TIMER) + " secs)? (y/n):"
        error = "Please press 'Y' or 'N' and then ENTER"
        choice = nml.two_choice_input_loop(prompt, "y", "n", error)
        if choice == "n":
            print "CSV Filename (exclude .csv extension):",
            filename = raw_input() + ".csv"
            print "Timer:",
            timer_string = raw_input()
            while not nml.is_number(timer_string):
                print "Please enter a valid number."
                print "Timer:",
                timer_string = raw_input()
            timer = float(timer_string)
            
        # Create a listener and controller
        listener = TapListener()
        controller = Leap.Controller()
        # Test for errors when opening the output file.
        try:
            writeFile = open(filename, 'w')
            writeFile.close()
        except:
            print "IO error.", filename, "most likely open somewhere else."
            return # Quit if there's an error
        
        height = nml.interaction_height(controller, False)
        print ""
        print "Place your hand with only your index finger extended about " 
        print str(height) + " inches above the controller."
        print "Start wagging and press Enter with your other hand to start..."
        raw_input()

        # Once added, the listener is able to disrupt any process with on_frame
        # method if it detects any data.
        controller.add_listener(listener)
        print "Reading data. . ."
        global start
        start = clock() # Start the clock to reference all measurements.

        # This empty loop runs until the time runs out. The listener's on_frame
        # method will execute every time the Leap senses an input.
        while (clock() - start < timer):
            pass
        # Remove the listener when done
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
        for row in data:
            for element in row:
                writeFile.write(str(element) + ',')
            writeFile.write('\n')
        writeFile.close()

        # Open data in Excel if desired
        prompt = "Open " + filename + " to view results? (y/n):"
        error = "Please press 'Y' or 'N' and then ENTER"
        if nml.two_choice_input_loop(prompt, "y", "n", error) == "y":
            system("start "+filename)
        prompt = "Run the program again? (y/n):"
        error = "Please press 'Y' or 'N' and then ENTER"
        if nml.two_choice_input_loop(prompt, "y", "n", error) == "n":
            return
        
# This independent statement should be at the bottom of all Python scripts
# that you wish to have a main() function.    
if __name__ == "__main__":
    main()
