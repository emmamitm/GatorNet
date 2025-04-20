import sys
import os
from pathlib import Path

# Get the absolute path to the home directory
HOME_DIR = Path(__file__).parent.parent.absolute()

# Add the path to the AI module
sys.path.insert(0, str(HOME_DIR / "chatbot" / "backend"))

# Set the AI_DATA_DIR environment variable for tests
os.environ["AI_DATA_DIR"] = str(HOME_DIR / "tests" / "mock_data")

print(f"Set up test paths. HOME_DIR = {HOME_DIR}")
print(f"AI module path = {HOME_DIR / 'chatbot' / 'backend'}")
print(f"AI_DATA_DIR = {os.environ['AI_DATA_DIR']}")
