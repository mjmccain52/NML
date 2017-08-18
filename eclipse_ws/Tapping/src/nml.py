"""Neuromechanics Lab Leap Support Functions

Author: Michael McCain
Last updated: 8/30/2013

Some functions I find to be particularly reusable
"""

def finger_positions_to_list(fingers):
        """Collects XYZ fingertip position data for all fingers and returns
        them as a single list [x,y,z,x,y,z,...]

        Keyword Argument:
        frame -- the list of Leap Vector objects containing finger positions
        """
        finger_list = []
        for finger in fingers:
                finger_list.extend(finger.tip_position.to_float_array())
        return finger_list
                
        
def is_in_interaction_box(frame, position):
        """Determines whether a single vector point falls within the Leap's
        preferred box of interaction. Returns True if so.

        Keyword arguments:
        frame -- a single frame of Leap data, used to determine the location
                 of the interaction box at the moment.
        position -- 3D vector representing a point above the Leap controller
        """
        
        box = frame.interaction_box

        c = box.center
        x_check = abs(c[0]- position[0]) < box.width / 2.0
        y_check = abs(c[1]- position[1]) < box.height / 2.0
        z_check = abs(c[2]- position[2]) < box.depth / 2.0
        return x_check and y_check and z_check
    
def two_choice_input_loop(prompt, choice_1, choice_2, error=""):
    """Generic process for looping until user selects one of two available
    choices. Returns valid choice 

    Keyword arguments:
    prompt -- Message instructing the user on two choices
    choice_1 -- first valid option, should be all lower case
    choice_2 -- second valid option, should be all lower case
    error (optional) -- Message to display when invalid choice is made.
                        No message by default.
    """
    
    chosen = False
    choice = ""
    while not chosen:
        print prompt
        # Change user input to lower case
        choice = str.lower(raw_input())
        if choice == choice_1 or choice == choice_2:
            chosen = True
        elif error != "":
            print error
    return choice

def is_number(num):
    """Determines if given string is a valid number, returns True if so.

    Keyword argument:
    num -- string to be tested
    """
    try:
        float(num)
        return True
    except ValueError:
        return False

def interaction_height(controller, metric=True):
    """Finds the ideal height for interaction above the Leap. Returns height in
    millimeters or inches or 0.0 if there's an error.

    Keyword arguments:
    controller -- instance of Leap.Controller
    metric (optional) -- True if millimeters are desired, False for inches
    """
    interaction_height = 0.0
    # Loop passes the time if the Leap still needs a moment to connect    
    while interaction_height == 0.0:
        interaction_height = controller.frame().interaction_box.center[1]
    if not metric:
        interaction_height = int(interaction_height / 25.4)

    return interaction_height
        
