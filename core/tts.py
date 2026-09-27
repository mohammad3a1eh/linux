import os

os.environ["ALLOW_PICKLE"] = "1"

import queue
import threading
import sounddevice as sd
from pathlib import Path
from kokoro_onnx import Kokoro


class PiperTTS:
    def __init__(self, model_path="models/tts/kokoro-v0_19.onnx", voices_path="models/tts/voices.bin"):

        if not Path(model_path).is_file() or not Path(voices_path).is_file():
            raise FileNotFoundError(f"Kokoro model files not found in {model_path} or {voices_path}")

        print("[TTS] Loading Kokoro-TTS engine...")
        self.kokoro = Kokoro(model_path, voices_path)

        # انتخاب صدای دخترانه آمریکایی (بسیار طبیعی و بااحساس)
        # گزینه‌های دیگر: 'af_sky', 'af_sarah', 'af_heart'
        self.voice_name = "af_sarah"

        self._queue = queue.Queue()
        self._stop = threading.Event()
        self._thread = None
        print("[TTS] Kokoro engine is ready!")

    def _worker(self):
        while not self._stop.is_set():
            try:
                text = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if text is None:
                continue

            try:
                # تولید صدا (سرعت 1.0 نرمال است)
                samples, sample_rate = self.kokoro.create(
                    text, voice=self.voice_name, speed=9.0, lang="en-us"
                )
                # پخش صدا با sounddevice
                sd.play(samples, sample_rate)
                sd.wait()
            except Exception as e:
                print(f"[TTS] error during playback: {e}")

    def _ensure_worker(self):
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(
                target=self._worker, name="kokoro-tts-worker", daemon=True
            )
            self._thread.start()

    def speak(self, text: str):
        """Queue text for synthesis+playback. Returns immediately."""
        if not text.strip():
            return
        self._ensure_worker()
        self._queue.put(text)

    def speak_blocking(self, text: str):
        """Synthesize and play synchronously (blocks caller)."""
        samples, sample_rate = self.kokoro.create(
            text, voice=self.voice_name, speed=1.0, lang="en-us"
        )
        sd.play(samples, sample_rate)
        sd.wait()

    def stop(self):
        """Clear pending speech and request worker exit after current item."""
        self._stop.set()
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._thread = None
        self._stop.clear()

    def close(self):
        self.stop()


if __name__ == "__main__":
    try:
        tts = PiperTTS()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)

    text = "Oh, hi! It's so nice to talk to you. I'm feeling great today!"
    print(f"Speaking: {text}")
    tts.speak_blocking(text)
    tts.close()