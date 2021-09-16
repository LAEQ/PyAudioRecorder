import wave
import alsaaudio
import pyaudio
from path import Path # NOTE: installer la lib path.py
from datetime import date, datetime, timedelta
import acoustics as ac
import numpy as np
import matplotlib.pyplot as plt
import copy

#################################################################################################
## Calibrating a recorded file from a calbiration file
#################################################################################################

folder = Path('/home/pi/Desktop/Audio_processing/PyAudioRecorder/test_folder')

s1 = ac.Signal.from_wav("/home/pi/Desktop/Audio_processing/PyAudioRecorder/test_folder/2021-09-16T16-56-16__2021-09-16T16-56-26_audio.wav")
s2 = ac.Signal.from_wav(folder.joinpath("2021-08-30T15-53-01__2021-08-30T15-53-11_audio.wav"))

s1.plot_power_spectrum()
plt.show()

s2.plot_power_spectrum()
plt.show()


s1.plot_spectrogram()
plt.show()

s2.plot_spectrogram()
plt.show()

s1.plot_levels()
plt.show()

# uncalibrated sound level
s2.plot_levels()
plt.show()

# calibrated sound level
s1c = s1.calibrate_to(94, inplace=False)
s2c = s2.calibrate_with(s1c, 94, inplace=False)
s2c.plot_levels()
plt.show()
