
# Helper functions for voice assistant.
# Dependencies for direct audio playback: sounddevice, numpy

# @title Helper functions (just run that cell)

import contextlib
import wave
import sounddevice as sd
import numpy as np
# from IPython.display import Audio # No longer used for playback in these functions

# Audio parameters (Gemini TTS typically outputs 24kHz, 16-bit PCM mono)
TTS_SAMPLE_RATE = 24000
TTS_CHANNELS = 1
# Assuming 16-bit PCM, so dtype='int16' for numpy array

# file_index = 0 # No longer needed if not saving files for playback

@contextlib.contextmanager
def wave_file(filename, channels=TTS_CHANNELS, rate=TTS_SAMPLE_RATE, sample_width=2):
    """Context manager to write to a WAV file."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width) # Corresponds to np.int16 if sample_width is 2
        wf.setframerate(rate)
        yield wf

def play_audio_blob(blob):
  """
  Plays audio data from a blob directly using sounddevice.
  Assumes blob.data contains raw PCM audio bytes.
  """
  if not hasattr(blob, 'data') or not blob.data:
      print("Error: Audio blob does not contain data.")
      return

  try:
      # Convert PCM bytes to NumPy array
      # Assuming 16-bit PCM data as is typical for WAV and Gemini TTS output
      audio_array = np.frombuffer(blob.data, dtype=np.int16)
      
      print(f"Playing audio using sounddevice (Sample Rate: {TTS_SAMPLE_RATE}, Inferred Channels: {audio_array.ndim})...")
      # sounddevice infers channels from the array shape (1D for mono, 2D for multi-channel)
      sd.play(audio_array, samplerate=TTS_SAMPLE_RATE)
      sd.wait() # Wait for playback to finish
      print("Audio playback finished.")
  except Exception as e:
      print(f"Error playing audio with sounddevice: {e}")

def play_audio(response):
    """
    Extracts audio blob from a Gemini response and plays it.
    """
    if response.candidates and response.candidates[0].content and \
       response.candidates[0].content.parts and \
       hasattr(response.candidates[0].content.parts[0], 'inline_data'):
        
        blob = response.candidates[0].content.parts[0].inline_data
        play_audio_blob(blob)
    else:
        print("Error: Could not extract audio data from Gemini response for playback.")
        # Optionally, log the response structure for debugging
        # print(f"Response structure: {str(response)[:500]}")