"""
Pytest configuration and shared fixtures for voice assistant tests.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key")
    yield


@pytest.fixture
def clean_audio_state():
    """Ensure clean audio state before and after tests"""
    # This fixture can be expanded to handle audio device cleanup if needed
    yield
    # Cleanup code here if needed