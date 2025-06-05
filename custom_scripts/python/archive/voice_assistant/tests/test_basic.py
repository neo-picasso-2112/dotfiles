#!/usr/bin/env python3
"""Basic tests to verify test infrastructure is working"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that basic imports work"""
    # Test that we can import basic modules
    import os
    import asyncio
    from rich.console import Console
    
    assert Console is not None


def test_environment():
    """Test that environment is set up correctly"""
    import os
    
    # We can check if GOOGLE_API_KEY would be available
    # (without requiring it for tests)
    assert True  # Basic test passes


def test_venv_creation():
    """Test that virtual environment exists"""
    venv_path = Path(__file__).parent.parent / ".venv"
    assert venv_path.exists()
    assert venv_path.is_dir()