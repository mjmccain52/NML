################################################################################
# Copyright (C) 2012-2013 Leap Motion, Inc. All rights reserved.               #
# Leap Motion proprietary and confidential. Not for distribution.              #
# Use subject to the terms of the Leap Motion SDK Agreement available at       #
# https://developer.leapmotion.com/sdk_agreement, or another agreement         #
# between Leap Motion and you, your company or other organization.             #
################################################################################

import Leap, sys, easygui
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture


class SampleListener(Leap.Listener):
    def on_init(self, controller):
        print "Initialized"

    def on_connect(self, controller):
        print "Connected"

    def on_disconnect(self, controller):
        # Note: not dispatched when running in a debugger.
        print "Disconnected"

    def on_exit(self, controller):
        print "Exited"

    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()

        if not frame.hands.empty:
            # Get the first hand
            hand = frame.hands[0]

            # Check if the hand has any fingers
            fingers = hand.fingers
            if not fingers.empty:
                # Calculate the hand's average finger tip position
                avg_pos = Leap.Vector()
                for finger in fingers:
                    avg_pos += finger.tip_position
                avg_pos /= len(fingers)
                print "Hand has %d fingers, average finger tip position: %s" % (
                      len(fingers), avg_pos)
            # Get the hand's normal vector and direction
            normal = hand.palm_normal
            direction = hand.direction

    def state_string(self, state):
        if state == Leap.Gesture.STATE_START:
            return "STATE_START"

        if state == Leap.Gesture.STATE_UPDATE:
            return "STATE_UPDATE"

        if state == Leap.Gesture.STATE_STOP:
            return "STATE_STOP"

        if state == Leap.Gesture.STATE_INVALID:
            return "STATE_INVALID"

def main():
    # Create a sample listener and controller
    listener = SampleListener()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)

    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    sys.stdin.readline()

    # Remove the sample listener when done
    controller.remove_listener(listener)


if __name__ == "__main__":
    main()
