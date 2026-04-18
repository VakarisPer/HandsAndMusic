import numpy as np
import librosa
import matplotlib.pyplot as plt
from IPython.display import Audio

AUDIO_FILE = "song.mp3"

y, sr = librosa.load(AUDIO_FILE)
fig, ax = plt.subplots()
melspec = librosa.power_to_db(librosa.feature.melspectrogram(y=y, sr=sr), ref=np.max)
librosa.display.specshow(melspec, y_axis='mel', x_axis='time', ax=ax)
ax.set(title='Mel spectrogram')

Audio(data=y, rate=sr)