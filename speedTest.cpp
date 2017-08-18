/******************************************************************************\
* Copyright (C) 2012-2013 Leap Motion, Inc. All rights reserved.               *
* Leap Motion proprietary and confidential. Not for distribution.              *
* Use subject to the terms of the Leap Motion SDK Agreement available at       *
* https://developer.leapmotion.com/sdk_agreement, or another agreement         *
* between Leap Motion and you, your company or other organization.             *
\******************************************************************************/

#include <iostream>
#include <vector>
#include "Leap.h"
using namespace Leap;


bool quit = false;
std::vector<Frame> frameList;
int64_t start = 0;

class SampleListener : public Listener {
  public:
    virtual void onFrame(const Controller&);
};

void SampleListener::onFrame(const Controller& controller) {
  // Get the most recent frame and report some basic information
  const Frame frame = controller.frame();
  frameList.push_back(frame);
  if (start == 0){
	  start = frame.timestamp();
  } else if (frame.timestamp() - start > 5000000){
	  quit = true;
  }

}

  

int main() {
  // Create a sample listener and controller
  SampleListener listener;
  Controller controller;

  // Have the sample listener receive events from the controller
  controller.addListener(listener);

  while (!quit){
	  continue;
  }
  int length = frameList.size();
  std::cout << length << std::endl;

  // Remove the sample listener when done
  controller.removeListener(listener);
  std::cin.get();
  return 0;
}
