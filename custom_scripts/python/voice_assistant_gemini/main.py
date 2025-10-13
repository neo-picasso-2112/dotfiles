#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "google-genai>=1.16.0",
#   "sounddevice",
#   "numpy",
# ]
# ///

"""
Live Audio Chat with Gemini using sounddevice

Provides real-time bidirectional audio conversation with text transcription.
Use headphones to prevent acoustic feedback.
"""

import asyncio
import sys
import traceback
import sounddevice as sd
import numpy as np
from google import genai
from google.genai import types

# ANSI color codes
class Colors:
    CYAN = '\033[96m'      # Bright cyan for streaming words
    WHITE = '\033[97m'     # Bright white for completed words  
    RESET = '\033[0m'      # Reset to default
    BOLD = '\033[1m'       # Bold text
    GREEN = '\033[92m'     # Green for status indicators
    YELLOW = '\033[93m'    # Yellow for processing status

class StatusDisplay:
    """Handles user interface status indicators"""
    def __init__(self):
        self.current_status = None
        self.line_needs_clear = False
    
    def show_listening(self):
        """Show that system is listening for user input"""
        if self.current_status != "listening":
            if self.line_needs_clear:
                print()  # New line to clear previous status
            print(f"\r🎤 {Colors.GREEN}{Colors.BOLD}Listening...{Colors.RESET}", end="", flush=True)
            self.current_status = "listening"
            self.line_needs_clear = True
    
    def show_speaking(self):
        """Show that Gemini is speaking"""
        if self.current_status != "speaking":
            if self.line_needs_clear:
                print()  # Clear listening status
            print(f"🔊 {Colors.YELLOW}{Colors.BOLD}Gemini speaking...{Colors.RESET}")
            self.current_status = "speaking"
            self.line_needs_clear = False
    
    def show_processing(self):
        """Show that system is processing"""
        if self.current_status != "processing":
            if self.line_needs_clear:
                print()
            print(f"\r🔄 {Colors.YELLOW}{Colors.BOLD}Processing...{Colors.RESET}", end="", flush=True)
            self.current_status = "processing"
            self.line_needs_clear = True
    
    def clear_status(self):
        """Clear current status line if needed"""
        if self.line_needs_clear:
            print("\r" + " " * 50 + "\r", end="", flush=True)
            self.line_needs_clear = False

# Suppress __pycache__ files
sys.dont_write_bytecode = True

if sys.version_info < (3, 11, 0):
    import taskgroup, exceptiongroup
    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup

CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

client = genai.Client()  # GOOGLE_API_KEY must be set as env variable

MODEL = "gemini-2.5-flash-preview-native-audio-dialog"
CONFIG = {
    "response_modalities": ["AUDIO"],
    "output_audio_transcription": {},
    "speech_config": {
        "voice_config": {"prebuilt_voice_config": {"voice_name": "Aoede"}}  # Available voices: Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr
    }
}


class AudioLoop:
    def __init__(self):
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.input_stream = None
        self.output_stream = None
        self.status_display = StatusDisplay()

    async def listen_audio(self):
        """Capture audio continuously for proper VAD"""
        loop = asyncio.get_event_loop()
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Input status: {status}")
            # Convert float32 to int16 PCM bytes
            audio_bytes = (indata[:, 0] * 32767).astype(np.int16).tobytes()
            
            # Send all audio continuously for VAD
            try:
                asyncio.run_coroutine_threadsafe(
                    self.out_queue.put({"data": audio_bytes, "mime_type": "audio/pcm"}),
                    loop
                )
            except:
                pass  # Drop if queue is full
        
        self.input_stream = sd.InputStream(
            channels=CHANNELS,
            samplerate=SEND_SAMPLE_RATE,
            blocksize=CHUNK_SIZE,
            dtype='float32',
            callback=audio_callback
        )
        
        self.input_stream.start()
        while True:
            await asyncio.sleep(0.1)

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send_realtime_input(audio=msg)

    async def receive_audio(self):
        """Handle responses with simple colored streaming and status indicators"""
        while True:
            turn = self.session.receive()
            turn_started = False
            
            async for response in turn:
                # Handle interruptions
                if hasattr(response, 'server_content') and response.server_content:
                    if hasattr(response.server_content, 'interrupted') and response.server_content.interrupted:
                        self.status_display.clear_status()
                        print(f"\n{Colors.BOLD}[Interrupted]{Colors.RESET}")
                        while not self.audio_in_queue.empty():
                            self.audio_in_queue.get_nowait()
                        turn_started = False
                        # Show listening status after interruption
                        self.status_display.show_listening()
                        continue
                    
                    # Stream transcription with colors - simple and reliable
                    if hasattr(response.server_content, 'output_transcription') and response.server_content.output_transcription:
                        if not turn_started:
                            self.status_display.show_speaking()
                            print(f"\n{Colors.BOLD}[Gemini]:{Colors.RESET} ", end="", flush=True)
                            turn_started = True
                        
                        # Show new text in cyan as it streams
                        print(f"{Colors.CYAN}{response.server_content.output_transcription.text}{Colors.RESET}", end="", flush=True)
                
                # Handle audio data
                if hasattr(response, 'data') and response.data:
                    self.audio_in_queue.put_nowait(response.data)

            # Turn completed - show listening status for next user input
            if turn_started:
                print()  # New line after Gemini's response
                self.status_display.show_listening()
            
            # Clear audio queue at end of turn
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()

    async def play_audio(self):
        """Direct audio streaming for real-time playback"""
        # Create output stream with float32 for better quality
        self.output_stream = sd.OutputStream(
            channels=CHANNELS,
            samplerate=RECEIVE_SAMPLE_RATE,
            dtype='float32',  # Use float32 for better quality
            blocksize=256,    # Even smaller blocks for lower latency
            latency='low'     # Request low latency mode
        )
        
        self.output_stream.start()
        
        try:
            while True:
                # Get audio data from queue
                audio_data = await self.audio_in_queue.get()
                if audio_data:
                    # Convert int16 bytes to float32 for playback
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    float_audio = audio_array.astype(np.float32) / 32768.0
                    # Write directly to stream
                    await asyncio.to_thread(self.output_stream.write, float_audio)
        except Exception as e:
            print(f"Playback error: {e}")
        finally:
            self.output_stream.stop()
            self.output_stream.close()

    async def run(self):
        print("🎙️ Starting Live API Native Audio Chat...")
        print("📡 Connecting to Gemini...")
        
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session

                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)
                
                print("✅ Connected! Ready for conversation.")
                print("💡 Tip: Use headphones to prevent audio feedback")
                
                # Show initial listening status
                self.status_display.show_listening()

                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())
        except asyncio.CancelledError:
            print("\n👋 Chat ended")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            traceback.print_exc()
        finally:
            if self.input_stream:
                self.input_stream.stop()
                self.input_stream.close()
            if self.output_stream:
                self.output_stream.stop()
                self.output_stream.close()


if __name__ == "__main__":
    try:
        asyncio.run(AudioLoop().run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
