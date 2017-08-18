clear all;
FILENAME = 'tapping.csv';
file = csvread(FILENAME,3,0); %Skip the headers.
t = file(:,1);
y = file(:,3);
plot(t,y)
peaks = findpeaks(y); %Built-in function
length(peaks) % reports how many peaks were found.
