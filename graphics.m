clear all
phi = 180*pi/180;

yT = [cos(phi)  0 sin(phi)
      0         1 0
      -sin(phi) 0 cos(phi)];
v = [1;1;1];
a = yT*v