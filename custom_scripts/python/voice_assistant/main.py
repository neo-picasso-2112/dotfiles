#!/usr/bin/env -S uv run --quiet --script

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
import time
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.align import Align
from rich.layout import Layout
from rich.rule import Rule
import sounddevice  # Import sounddevice FIRST to initialize PortAudio
from RealtimeSTT import AudioToTextRecorder
import logging

# Suppress RealtimeSTT debug logs
logging.getLogger("RealtimeSTT").setLevel(logging.ERROR)
logging.getLogger("faster_whisper").setLevel(logging.ERROR)

# Initialize console for rich output
console = Console()

# ASCII Art for Voice Assistant
VOICE_ASSISTANT_LOGO = """
██    ██  ██████  ██  ██████ ███████ 
██    ██ ██    ██ ██ ██      ██      
██    ██ ██    ██ ██ ██      █████   
 ██  ██  ██    ██ ██ ██      ██      
  ████    ██████  ██  ██████ ███████ 

 █████  ███████ ███████ ██ ███████ ████████  █████  ███    ██ ████████ 
██   ██ ██      ██      ██ ██         ██    ██   ██ ████   ██    ██    
███████ ███████ ███████ ██ ███████    ██    ███████ ██ ██  ██    ██    
██   ██      ██      ██ ██      ██    ██    ██   ██ ██  ██ ██    ██    
██   ██ ███████ ███████ ██ ███████    ██    ██   ██ ██   ████    ██    
"""

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def show_welcome_screen():
    """Display the welcome screen with logo and instructions"""
    clear_screen()
    
    # Create the main welcome panel
    welcome_content = Text()
    welcome_content.append("Welcome to the ", style="white")
    welcome_content.append("Voice Assistant", style="bold #FF6B35")
    welcome_content.append(" research preview!", style="white")
    
    welcome_panel = Panel(
        Align.center(welcome_content),
        style="#FF6B35",
        padding=(0, 2)
    )
    
    # Display logo
    logo_panel = Panel(
        Align.center(Text(VOICE_ASSISTANT_LOGO, style="bold #FF6B35")),
        style="#FF6B35",
        padding=(1, 2)
    )
    
    # Status message
    status_text = Text()
    status_text.append("🎉 Login successful. Press ", style="cyan")
    status_text.append("Enter", style="bold white")
    status_text.append(" to continue", style="cyan")
    
    console.print(welcome_panel)
    console.print()
    console.print(logo_panel)
    console.print()
    console.print(Align.center(status_text))
    
    # Wait for user input
    input()

def show_interface_header():
    """Show the main interface header"""
    clear_screen()
    
    # Header with title
    header = Panel(
        Align.center(Text("🎙️ Voice Assistant STT", style="bold #FF6B35")),
        style="#FF6B35",
        padding=(0, 2)
    )
    console.print(header)
    console.print()
    
    # Instructions table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="#FF6B35")
    table.add_column(style="white")
    
    table.add_row("•", "Press Enter to start recording")
    table.add_row("•", "Press Enter again to stop recording") 
    table.add_row("•", "Press Ctrl+C to exit")
    
    instruction_panel = Panel(
        table,
        title="Instructions",
        title_align="left",
        style="#FF6B35",
        padding=(1, 2)
    )
    
    console.print(instruction_panel)
    console.print()

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
        # Show initialization status
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing Voice Transcriber...", total=None)
            
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
            
            progress.update(task, description="Voice Transcriber ready!")
            time.sleep(0.5)  # Brief pause to show completion
        
        self.current_text = ""
        self.is_recording = False
        
        # Success message
        success_panel = Panel(
            Text("✅ Voice Transcriber initialized successfully!", style="bold green"),
            style="green",
            padding=(0, 2)
        )
        console.print(success_panel)
        console.print()
    
    def _on_realtime_update(self, text: str):
        """Handle real-time transcription updates"""
        self.current_text = text
        # Clear line and update with new text with better formatting
        sys.stdout.write('\r' + ' ' * 100 + '\r')  # Clear line
        
        # Format the recording text with color codes
        recording_text = f"\033[1;33m🎤 Recording: \033[0m\033[1;37m{text}\033[0m"
        sys.stdout.write(recording_text)
        sys.stdout.flush()
    
    def listen(self) -> str:
        """
        Record audio and return the transcribed text
        
        Returns:
            str: The transcribed text from the audio
        """
        self.is_recording = True
        self.current_text = ""
        
        # Show recording status panel
        recording_panel = Panel(
            Text("🎤 Recording... (Press Enter to stop)", style="bold yellow"),
            style="yellow",
            padding=(0, 2)
        )
        console.print(recording_panel)
        
        # Variable to store the final transcription
        final_text = ""
        
        def process_text(text: str):
            """Callback for when recording is complete"""
            nonlocal final_text
            final_text = text
            if text:
                # Clear the recording line
                sys.stdout.write('\r' + ' ' * 100 + '\r')
                sys.stdout.flush()
                
                # Show completion status
                completion_panel = Panel(
                    Text("✅ Transcription complete", style="bold green"),
                    style="green",
                    padding=(0, 2)
                )
                console.print(completion_panel)
        
        # Start recording with callback
        self.recorder.text(process_text)
        
        self.is_recording = False
        return final_text
    
    def shutdown(self):
        """Shutdown the recorder and clean up resources"""
        if hasattr(self, 'recorder') and self.recorder:
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Shutting down recorder...", total=None)
                    self.recorder.shutdown()
                    progress.update(task, description="Recorder shutdown complete")
                    time.sleep(0.3)
            except Exception as e:
                error_panel = Panel(
                    Text(f"Error during shutdown: {e}", style="bold red"),
                    style="red",
                    padding=(0, 2)
                )
                console.print(error_panel)


async def main():
    """Main application loop"""
    # Show welcome screen first
    show_welcome_screen()
    
    # Show main interface
    show_interface_header()
    
    # Initialize transcriber
    transcriber = VoiceTranscriber()
    
    try:
        while True:
            # Show prompt for user input
            prompt_panel = Panel(
                Text("Press Enter to start recording", style="bold cyan"),
                style="cyan",
                padding=(0, 2)
            )
            console.print(prompt_panel)
            
            # Wait for user to press Enter
            input()
            
            # Record and transcribe
            transcription = transcriber.listen()
            
            if transcription:
                # Display the final transcription in a styled panel
                transcription_panel = Panel(
                    Text(transcription, style="white"),
                    title="📝 Transcription",
                    title_align="left",
                    style="#FF6B35",
                    padding=(1, 2)
                )
                console.print(transcription_panel)
            else:
                # Show no speech detected message
                no_speech_panel = Panel(
                    Text("No speech detected", style="yellow"),
                    style="yellow", 
                    padding=(0, 2)
                )
                console.print(no_speech_panel)
            
            console.print()  # Add spacing
            
    except KeyboardInterrupt:
        console.print()
        exit_panel = Panel(
            Text("Exiting Voice Assistant...", style="bold red"),
            style="red",
            padding=(0, 2)
        )
        console.print(exit_panel)
    finally:
        transcriber.shutdown()
        goodbye_panel = Panel(
            Text("Goodbye! 👋", style="bold cyan"),
            style="cyan",
            padding=(0, 2)
        )
        console.print(goodbye_panel)


if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass