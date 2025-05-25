# scribe/config.py
from pathlib import Path

# Base for NON-DAILY notes (within knowledge_base)
KB_BASE_DIR = Path("~/repos/second-brain/knowledge_base").expanduser()
# Base specifically FOR DAILY notes (directly under second_brain)
DAILY_BASE_DIR = Path("~/repos/second-brain").expanduser()
# Location of templates
TEMPLATES_BASE_DIR = Path("~/repos/second-brain/templates").expanduser()
