#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "google-genai>=1.16.0", # 1.16 is needed for multi-speaker audio
#   "sounddevice",
#   "numpy",
#   "RealtimeSTT",
#   "rich",
#   "PyAudio",
#   "pytest",  # For running tests
# ]
# ///

"""
Voice Assistant with Real-time Speech-to-Text

This module provides real-time audio recording and transcription functionality
using RealtimeSTT. It records audio from the microphone and displays the
transcription in real-time.

Usage:
    ./main.py
    
    Press Enter to start recording, and Enter again to stop.
    Press Ctrl+C to exit.
"""

import os
import sys
import asyncio
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
import sounddevice  # Import sounddevice FIRST to initialize PortAudio
from RealtimeSTT import AudioToTextRecorder
import logging

# Suppress RealtimeSTT debug logs
logging.getLogger("RealtimeSTT").setLevel(logging.ERROR)
logging.getLogger("faster_whisper").setLevel(logging.ERROR)

# Initialize console for rich output
console = Console()

# Check for required environment variable (keeping for future TTS integration)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    console.print("[bold red]Error: GOOGLE_API_KEY environment variable not set.[/bold red]")
    console.print("Please set it in your .env file or as an environment variable.")
    sys.exit(1)

# Previous TTS code (commented out as requested)
"""
from google import genai
from google.genai import types as genai_types
from helper import play_audio

# Audio parameters (Gemini TTS typically outputs 24kHz, 16-bit PCM mono)
TTS_SAMPLE_RATE = 24000
TTS_CHANNELS = 1

# Configure the Gemini client with the API key
client = genai.Client(api_key=GOOGLE_API_KEY)

VOICE_NAME = "Sadaltager"
CONTENTS="Hi, please generate a short (like 100 words) transcript..."
MODEL_ID = "gemini-2.5-flash-preview-tts"

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
"""


class VoiceTranscriber:
    """Handles real-time audio recording and transcription"""
    
    def __init__(self):
        """Initialize the voice transcriber with RealtimeSTT"""
        console.print("[bold blue]Initializing Voice Transcriber...[/bold blue]")
        
        # Initialize the recorder with optimized settings for real-time transcription
        self.recorder = AudioToTextRecorder(
            model="tiny.en",  # Fast model for real-time performance
            language="en",
            compute_type="float32",
            enable_realtime_transcription=True,
            realtime_model_type="tiny.en",
            post_speech_silence_duration=0.8,
            realtime_processing_pause=0.2,
            on_realtime_transcription_update=self._on_realtime_update,
            spinner=False,
            print_transcription_time=False,
        )
        
        self.current_text = ""
        self.is_recording = False
        console.print("[bold green]Voice Transcriber ready![/bold green]")
    
    def _on_realtime_update(self, text: str):
        """Handle real-time transcription updates"""
        self.current_text = text
        # Clear line and update with new text
        sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear line
        sys.stdout.write(f"🎤 Recording: {text}")
        sys.stdout.flush()
    
    def listen(self) -> str:
        """
        Record audio and return the transcribed text
        
        Returns:
            str: The transcribed text from the audio
        """
        self.is_recording = True
        self.current_text = ""
        
        console.print("\n[bold yellow]🎤 Recording... (Press Enter to stop)[/bold yellow]")
        
        # Variable to store the final transcription
        final_text = ""
        
        def process_text(text: str):
            """Callback for when recording is complete"""
            nonlocal final_text
            final_text = text
            if text:
                console.print(f"\n[bold green]✓ Transcription complete[/bold green]")
        
        # Start recording with callback
        self.recorder.text(process_text)
        
        self.is_recording = False
        return final_text
    
    def shutdown(self):
        """Shutdown the recorder and clean up resources"""
        if hasattr(self, 'recorder') and self.recorder:
            try:
                self.recorder.shutdown()
                console.print("[bold blue]Recorder shutdown complete[/bold blue]")
            except Exception as e:
                console.print(f"[bold red]Error during shutdown: {e}[/bold red]")


async def main():
    """Main application loop"""
    console.print(Panel.fit(
        "[bold magenta]🎙️  Real-time Voice Transcriber[/bold magenta]\n\n"
        "Press [bold]Enter[/bold] to start recording\n"
        "Press [bold]Enter[/bold] again to stop recording\n"
        "Press [bold]Ctrl+C[/bold] to exit",
        title="Voice Assistant STT",
        border_style="magenta"
    ))
    
    transcriber = VoiceTranscriber()
    
    try:
        while True:
            # Wait for user to press Enter
            input("\n[Press Enter to start recording]")
            
            # Record and transcribe
            transcription = transcriber.listen()
            
            if transcription:
                # Display the final transcription in a nice panel
                console.print(Panel(
                    transcription,
                    title="📝 Transcription",
                    border_style="green",
                    padding=(1, 2)
                ))
            else:
                console.print("[yellow]No speech detected[/yellow]")
            
    except KeyboardInterrupt:
        console.print("\n[bold red]Exiting...[/bold red]")
    finally:
        transcriber.shutdown()
        console.print("[bold]Goodbye! 👋[/bold]")


if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass