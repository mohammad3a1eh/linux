"""Offline Persian Speech-to-Text using Vosk + sounddevice."""

import json
import queue
import threading
import time
from pathlib import Path

import vosk
from vosk import KaldiRecognizer, Model, SetLogLevel

from config import STT_MODEL_PATH

SAMPLE_RATE = 16000
_CHANNELS = 1
_CHUNK_MS = 30
_CHUNK_FRAMES = int(SAMPLE_RATE * _CHUNK_MS / 1000)
_BYTES_PER_FRAME = 2

_MODEL_URL = "https://alphacephei.com/vosk/models"


class VoskSTT:
    def __init__(self, model_path=STT_MODEL_PATH, sample_rate=SAMPLE_RATE):
        self.model_path = Path(model_path)
        if not self.model_path.is_dir():
            raise FileNotFoundError(
                f"Vosk model not found at {self.model_path!s}. "
                f"Download the Persian model from {_MODEL_URL} and extract it there."
            )
        self.sample_rate = sample_rate

        SetLogLevel(-1)
        self._model = Model(str(self.model_path))
        self._recognizer = KaldiRecognizer(self._model, self.sample_rate)
        self._recognizer.SetWords(True)

        self._frame_q = queue.Queue()
        self._stop = threading.Event()
        self._stream = None
        self._device = None

    def _audio_callback(self, indata, _frames, _time, status):
        if status:
            print(f"[stt] audio status: {status}", flush=True)
        self._frame_q.put(bytes(indata))

    def _start_stream(self):
        try:
            import sounddevice as sd
        except OSError as exc:
            raise OSError(
                "sounddevice needs PortAudio: install libportaudio2 "
                "(sudo apt install libportaudio2)"
            ) from exc

        self._device = sd
        self._stop.clear()
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=_CHANNELS,
            dtype="int16",
            blocksize=_CHUNK_FRAMES,
            callback=self._audio_callback,
        )
        self._stream.start()

    def listen(self, timeout_seconds: float = 5.0):
        """Yield Persian sentence text as soon as Vosk finalizes one.

        Yields nothing and returns early if no speech is detected within
        *timeout_seconds* (measured from the start of the audio stream).
        """
        self._start_stream()
        start = time.monotonic()
        try:
            while not self._stop.is_set():
                if (time.monotonic() - start) > timeout_seconds:
                    return
                try:
                    frame = self._frame_q.get(timeout=0.1)
                except queue.Empty:
                    continue
                if self._recognizer.AcceptWaveform(frame):
                    result = json.loads(self._recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        yield text
                        start = time.monotonic()
        finally:
            self.stop()

    def finalize(self):
        """Return whatever text was recognized since the last final result."""
        result = json.loads(self._recognizer.FinalResult())
        return result.get("text", "").strip()

    def stop(self):
        self._stop.set()
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass

    def close(self):
        self.stop()


if __name__ == "__main__":
    try:
        stt = VoskSTT()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)

    print("Listening… press Ctrl+C to stop.")
    try:
        for sentence in stt.listen():
            print(f">> {sentence}", flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        stt.stop()