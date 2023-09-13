from model import snowboydecoder
from model.config import MODEL, SENSITIVITY
from model.call_vosk import assis

detector = False

detector = snowboydecoder.HotwordDetector(MODEL, sensitivity=SENSITIVITY)
detector.start(
    detected_callback= assis,
    # interrupt_check= ,
    # sleep_time= ,
)
detector.terminate()