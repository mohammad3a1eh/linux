from model import snowboydecoder
from model.config import MODEL, SENSITIVITY
from model.call_vosk import assis
import os
from subprocess import run

# Grant X11 access for current user (if not already granted)
# for fix Xlib.error.DisplayConnectionError in my debian
try:
    run(['xhost', '+SI:localuser:' + os.getlogin()], check=True)
except Exception as e:
    print(f"Failed to set xhost permissions: {e}")

detector = False

detector = snowboydecoder.HotwordDetector(MODEL, sensitivity=SENSITIVITY)
detector.start(
    detected_callback= assis,
)
detector.terminate()