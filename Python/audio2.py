import alsaaudio
import wave
import array
wav_output_filename = 'test2.wav' # name of .wav file


CHANNELS = 1
INFORMAT = alsaaudio.PCM_FORMAT_S16_LE
RATE = 48000
FRAMESIZE = 4096
record_secs=10

# set up audio input
recorder=alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE)
recorder.setchannels(CHANNELS)
recorder.setrate(RATE)
recorder.setformat(INFORMAT)
recorder.setperiodsize(FRAMESIZE)


frames = []
for ii in range(0,int((RATE/FRAMESIZE)*record_secs)):
    frames.append(recorder.read()[1])


# save the audio frames as .wav file
wavefile = wave.open(wav_output_filename,'wb')
wavefile.setnchannels(CHANNELS)
wavefile.setsampwidth(2)
wavefile.setframerate(RATE)
wavefile.writeframes(b''.join(frames))
wavefile.close()
