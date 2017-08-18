"""Finger Oscillation Test

Author: Michael McCain
Last updated: 8/29/2013

Uses the Leap Motion controller to gather data from user tapping finger and
thumb together rapidly.
"""

import Leap, sys, time
from time import clock

y_data = [] # vertical postion data is stored here until ready to write to file.
TIMER = 5
FILENAME = "tapping.csv"

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
        if not frame.hands.is_empty:
            hand = frame.hands[0]
            fingers = hand.fingers
            if not fingers.is_empty:
                frame_data = [clock() - start] # Row to be added to y_data
                for finger in fingers:
                    frame_data.append(finger.tip_position[1])
                y_data.append(frame_data)

def main():

    # Create a listener and controller
    listener = TapListener()
    controller = Leap.Controller()
    # Test for errors when opening the output file.
    try:
        writeFile = open(FILENAME, 'w')
        writeFile.close()
    except:
        print "IO error.", FILENAME, "most likely open somewhere else."
        return # Quit if there's an error
    
    print "Press Enter to start..."
    sys.stdin.readline()

    # Once added, the listener is able to disrupt any process with on_frame
    # method if it detects any data.
    controller.add_listener(listener)
    global start
    start = clock() # Start the clock to reference all measurements.

    # This empty loop runs until the time runs out. The listener's on_frame
    # method will execute every time the Leap senses an input.
    while (clock() - start < TIMER):
        pass
    # Remove the listener when done
    controller.remove_listener(listener)

    writeFile = open(FILENAME, 'w')
    writeFile.write ('Y-position Data for Tapping Exercise\n' + \
                     'Time (s),' + \
                     'Finger 1,' + \
                     'Finger 2,' + \
                     'Finger 3,' + \
                     'Finger 4,' + \
                     'Finger 5\n')
    # Write the gathered data to file
    for row in y_data:
        for element in row:
            writeFile.write(str(element) + ',')
        writeFile.write('\n')
    writeFile.close()
            
# This independent statement should be at the bottom of all Python scripts
# that you wish to have a main().    
if __name__ == "__main__":
    main()
