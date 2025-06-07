"""
Pytest configuration and shared fixtures for voice assistant tests.
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables before any imports
os.environ["GOOGLE_API_KEY"] = "test-key-for-testing"


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing - automatically applied to all tests"""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-for-testing")
    yield


@pytest.fixture
def clean_audio_state():
    """Ensure clean audio state before and after tests"""
    # This fixture can be expanded to handle audio device cleanup if needed
    yield
    # Cleanup code here if needed


# Additional fixtures can be added here as needed