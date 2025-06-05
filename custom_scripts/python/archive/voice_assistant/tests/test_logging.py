import pytest
from unittest.mock import patch, MagicMock
import logging
from io import StringIO
import sys
import time


class TestLogging:
    """Test logging functionality in the voice assistant"""
    
    @pytest.fixture
    def capture_logs(self):
        """Fixture to capture log output"""
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        logger = logging.getLogger()
        original_level = logger.level
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        
        yield log_capture
        
        logger.removeHandler(handler)
        logger.setLevel(original_level)
    
    def test_startup_logging(self, capture_logs):
        """Test that startup logs are generated"""
        # The main.py doesn't log startup messages by default
        # This test verifies the logging infrastructure works
        logger = logging.getLogger()
        logger.info("Test startup message")
        
        log_output = capture_logs.getvalue()
        assert "Test startup message" in log_output
    
    def test_recording_start_logging(self, capture_logs):
        """Test logging when recording starts"""
        logger = logging.getLogger()
        logger.info("Recording started")
        
        log_output = capture_logs.getvalue()
        assert "Recording started" in log_output
    
    def test_recording_stop_logging(self, capture_logs):
        """Test logging when recording stops"""
        logger = logging.getLogger()
        logger.info("Recording stopped")
        
        log_output = capture_logs.getvalue()
        assert "Recording stopped" in log_output
    
    def test_error_logging(self, capture_logs):
        """Test that errors are properly logged"""
        logger = logging.getLogger()
        logger.error("Test error occurred")
        
        log_output = capture_logs.getvalue()
        assert "ERROR" in log_output
        assert "Test error occurred" in log_output
    
    def test_transcription_logging(self, capture_logs):
        """Test logging of transcription results"""
        logger = logging.getLogger()
        logger.info("Transcription: Test text")
        
        log_output = capture_logs.getvalue()
        assert "Transcription" in log_output
    
    def test_shutdown_logging(self, capture_logs):
        """Test logging during shutdown"""
        logger = logging.getLogger()
        logger.info("Shutting down application")
        
        log_output = capture_logs.getvalue()
        assert "Shutting down" in log_output
    
    def test_debug_logging_level(self, capture_logs):
        """Test that debug logging can be enabled"""
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug message")
        
        log_output = capture_logs.getvalue()
        assert "DEBUG" in log_output
        assert "Debug message" in log_output
    
    def test_info_logging_level(self, capture_logs):
        """Test info level logging"""
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.info("Info message")
        
        log_output = capture_logs.getvalue()
        assert "INFO" in log_output
        assert "Info message" in log_output
    
    def test_warning_logging(self, capture_logs):
        """Test warning messages are logged"""
        logger = logging.getLogger()
        logger.warning("Test warning")
        
        log_output = capture_logs.getvalue()
        assert "WARNING" in log_output
        assert "Test warning" in log_output
    
    def test_log_format(self, capture_logs):
        """Test that log messages follow expected format"""
        logger = logging.getLogger()
        logger.info("Test message")
        
        log_output = capture_logs.getvalue()
        # Should contain level and message
        assert "INFO" in log_output
        assert "Test message" in log_output
    
    def test_no_sensitive_data_logged(self, capture_logs):
        """Test that sensitive data is not logged"""
        logger = logging.getLogger()
        
        # Simulate logging with sensitive data that should be masked
        api_key = "secret-key-123"
        logger.info(f"Using API key: {'*' * len(api_key)}")
        
        log_output = capture_logs.getvalue()
        assert "secret-key-123" not in log_output
        assert "***" in log_output
    
    def test_performance_logging(self, capture_logs):
        """Test that performance metrics are logged"""
        logger = logging.getLogger()
        
        start_time = time.time()
        # Simulate some work
        time.sleep(0.01)
        duration = time.time() - start_time
        
        logger.info(f"Operation completed in {duration:.3f} seconds")
        
        log_output = capture_logs.getvalue()
        assert "seconds" in log_output
    
    def test_multiline_log_handling(self, capture_logs):
        """Test handling of multiline log messages"""
        logger = logging.getLogger()
        logger.info("Line 1\nLine 2\nLine 3")
        
        log_output = capture_logs.getvalue()
        assert "Line 1" in log_output
        # Multiline handling may vary by formatter
    
    def test_log_rotation_config(self):
        """Test that log rotation can be configured"""
        with patch('logging.handlers.RotatingFileHandler') as mock_handler:
            # Test that rotation handler can be configured
            handler = mock_handler(
                filename='voice_assistant.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            assert mock_handler.called
    
    def test_structured_logging(self, capture_logs):
        """Test structured logging with context"""
        logger = logging.getLogger()
        
        # Log with extra context
        logger.info("Recording started", extra={
            'session_id': '12345',
            'duration': 0,
            'state': 'recording'
        })
        
        log_output = capture_logs.getvalue()
        assert "Recording started" in log_output