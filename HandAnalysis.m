clear all;
FILENAME = 'handData.csv';
file = csvread(FILENAME);
% Save a vector with sample times, first time is 0
t_orig = file(:,1) - file(1,1);
num = length(t_orig);
% Find all differences between sample times
differences = zeros(num-1,1);
for i = 2:num
    differences(i-1) = t_orig(i) - t_orig(i-1);
end
% Find average difference for uniform sampling
dt = mean(differences);
% Save x positions
x_orig = file(:,2);
% Fill vector with evenly spaced sample times
t = 0:dt:t_orig(num);
t = t.';
%Interpolate original data
x = interp1(t_orig,x_orig,t);

%Fourier
n = pow2(nextpow2(num)); %Transform Length
y = fft(x,n); %DFT
f = (0:n-1)/(dt*n); %frequency range
power = y.*conj(y)/n; %Power of the DFT

plot(f,abs(y))
xlabel('Frequency (Hz)')
ylabel('Power')
title('{\bf Periodogram}')


