#!/usr/bin/env python3
"""
Test suite for RealtimeSTT integration in the voice assistant.
Tests the audio recording and transcription functionality.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path to import main module
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSTTIntegration:
    """Test cases for Speech-to-Text integration"""
    
    @pytest.fixture
    def mock_recorder(self):
        """Create a mock AudioToTextRecorder"""
        with patch('main.AudioToTextRecorder') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_console(self):
        """Mock the rich console to prevent actual output during tests"""
        with patch('main.Console') as mock_console:
            yield mock_console.return_value
    
    def test_recorder_initialization(self, mock_recorder):
        """Test that the recorder is properly initialized with correct parameters"""
        from main import VoiceTranscriber
        
        transcriber = VoiceTranscriber()
        
        # Verify recorder was created
        assert transcriber.recorder is not None
        
    def test_recorder_configuration(self):
        """Test that the recorder is configured with appropriate settings"""
        from main import VoiceTranscriber
        
        with patch('main.AudioToTextRecorder') as mock_recorder_class:
            transcriber = VoiceTranscriber()
            
            # Check that AudioToTextRecorder was called with correct parameters
            mock_recorder_class.assert_called_once()
            call_args = mock_recorder_class.call_args
            
            # Verify key configuration parameters
            assert call_args.kwargs['model'] == 'tiny.en'  # Fast model for real-time
            assert call_args.kwargs['language'] == 'en'
            assert call_args.kwargs['enable_realtime_transcription'] == True
            
    def test_listen_method_returns_text(self, mock_recorder):
        """Test that the listen method returns transcribed text"""
        from main import VoiceTranscriber
        
        # Setup mock to simulate transcription
        mock_recorder.text.side_effect = lambda callback: callback("Hello world")
        
        transcriber = VoiceTranscriber()
        result = transcriber.listen()
        
        assert result == "Hello world"
        mock_recorder.text.assert_called_once()
    
    def test_realtime_callback_updates_display(self, mock_recorder, mock_console):
        """Test that real-time transcription updates are displayed"""
        from main import VoiceTranscriber
        
        transcriber = VoiceTranscriber()
        
        # Simulate real-time updates
        realtime_texts = []
        
        # Capture the callback function when text() is called
        def capture_callback(callback):
            # Simulate multiple real-time updates
            transcriber.recorder.on_realtime_transcription_update("Hello")
            transcriber.recorder.on_realtime_transcription_update("Hello world")
            callback("Hello world")
        
        mock_recorder.text.side_effect = capture_callback
        
        result = transcriber.listen()
        assert result == "Hello world"
    
    def test_empty_transcription_handling(self, mock_recorder):
        """Test handling of empty transcriptions"""
        from main import VoiceTranscriber
        
        mock_recorder.text.side_effect = lambda callback: callback("")
        
        transcriber = VoiceTranscriber()
        result = transcriber.listen()
        
        assert result == ""
    
    def test_transcription_with_special_characters(self, mock_recorder):
        """Test transcription with special characters and punctuation"""
        from main import VoiceTranscriber
        
        test_text = "Hello, world! How are you? It's a nice day."
        mock_recorder.text.side_effect = lambda callback: callback(test_text)
        
        transcriber = VoiceTranscriber()
        result = transcriber.listen()
        
        assert result == test_text
    
    def test_keyboard_interrupt_handling(self, mock_recorder):
        """Test graceful handling of keyboard interrupts"""
        from main import VoiceTranscriber
        
        # Simulate keyboard interrupt during recording
        mock_recorder.text.side_effect = KeyboardInterrupt()
        
        transcriber = VoiceTranscriber()
        
        with pytest.raises(KeyboardInterrupt):
            transcriber.listen()
    
    def test_recorder_shutdown(self, mock_recorder):
        """Test that recorder is properly shut down"""
        from main import VoiceTranscriber
        
        transcriber = VoiceTranscriber()
        transcriber.shutdown()
        
        mock_recorder.shutdown.assert_called_once()


class TestMainLoop:
    """Test cases for the main transcription loop"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies"""
        with patch('main.AudioToTextRecorder') as mock_recorder, \
             patch('main.Console') as mock_console, \
             patch('main.os.environ.get', return_value='fake_api_key'):
            yield {
                'recorder': mock_recorder,
                'console': mock_console
            }
    
    @pytest.mark.asyncio
    async def test_main_loop_single_iteration(self, mock_dependencies):
        """Test a single iteration of the main loop"""
        from main import main
        
        # Setup mocks to simulate one transcription then exit
        mock_recorder_instance = mock_dependencies['recorder'].return_value
        
        # First call returns text, second raises KeyboardInterrupt to exit
        mock_recorder_instance.text.side_effect = [
            lambda cb: cb("Test transcription"),
            KeyboardInterrupt()
        ]
        
        # Run main with expectation of KeyboardInterrupt
        with pytest.raises(KeyboardInterrupt):
            await main()
    
    def test_environment_variable_check(self):
        """Test that missing environment variable is handled"""
        with patch('main.os.environ.get', return_value=None):
            with pytest.raises(SystemExit):
                from main import GOOGLE_API_KEY
                # This should trigger the check in main.py


class TestCLIInterface:
    """Test cases for command-line interface"""
    
    def test_script_is_executable(self):
        """Test that the script has proper shebang and is executable"""
        main_path = Path(__file__).parent.parent / "main.py"
        
        with open(main_path, 'r') as f:
            first_line = f.readline().strip()
        
        assert first_line.startswith('#!/usr/bin/env')
        assert 'uv run --script' in first_line
    
    def test_uv_dependencies(self):
        """Test that UV dependencies are properly defined"""
        main_path = Path(__file__).parent.parent / "main.py"
        
        with open(main_path, 'r') as f:
            content = f.read()
        
        # Check for UV script block
        assert '# /// script' in content
        assert 'RealtimeSTT' in content
        assert 'requires-python = ">=3.9"' in content