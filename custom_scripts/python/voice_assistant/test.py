#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "google-genai>=1.16.0", # 1.16 is needed for multi-speaker audio
#   "sounddevice",
#   "numpy",
# ]
# ///

import os
from google import genai # This import style was in the file, keeping it.
from google.genai import types as genai_types # Using alias for clarity
from helper import play_audio

# Audio parameters (Gemini TTS typically outputs 24kHz, 16-bit PCM mono)
TTS_SAMPLE_RATE = 24000
TTS_CHANNELS = 1
# Assuming 16-bit PCM, so dtype='int16' for numpy array

# Get Google API Key from environment variable
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
VOICE_NAME = "Sadaltager" # @param ["Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede", "Callirhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba", "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar", "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird", "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafar"]
CONTENTS="""
      Hi, please generate a short (like 100 words) transcript that feels like a podcast between an irish person and a pirate discussing the political complexities surrounding the Trump administration.
"""
if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    exit(1)

# Configure the Gemini client with the API key
client = genai.Client(api_key=GOOGLE_API_KEY)

MODEL_ID = "gemini-2.5-flash-preview-tts" # @param ["gemini-2.5-flash-preview-tts","gemini-2.5-pro-preview-tts"] {"allow-input":true, isTemplate: true}


transcript = client.models.generate_content(
    model='gemini-2.5-flash-preview-05-20',
    contents=CONTENTS
  ).text

print(transcript)

response = client.models.generate_content(
  model=MODEL_ID,
  contents=transcript,
  config=genai_types.GenerateContentConfig(
    response_modalities=["AUDIO"],
    speech_config=genai_types.SpeechConfig(
        voice_config=genai_types.VoiceConfig(
            prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(
                voice_name=VOICE_NAME,
            )
        )
    ),
  )
)

play_audio(response)
