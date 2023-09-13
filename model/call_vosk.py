from vosk import Model, KaldiRecognizer
from model.config import PATH_VOSK
import pyaudio
import json
from model.controller import controller
import time
from model.scripts import play



def assis():
    play("yes")
    stt = time.time()
    print(stt)
    model = Model(PATH_VOSK)

    recognizeren = KaldiRecognizer(model, 48000)
    cap = pyaudio.PyAudio()
    stream = cap.open(format=pyaudio.paInt16, channels=1,
                        rate=48000, input=True, frames_per_buffer=4096)
    stream.start_stream()
    while True:
        result = None
        stream_value = stream.read(4096)
        if recognizeren.AcceptWaveform(stream_value):
            result = recognizeren.Result()
            result = json.loads(result)
            result = result["text"]
            _ = controller(result, stt)
            if not _:
                break