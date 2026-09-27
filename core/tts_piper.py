"""Offline Persian Text-to-Speech using piper-tts.

Synthesis runs in a background worker thread so `speak()` never blocks the
GTK main loop. Audio is played with sounddevice (PortAudio), falling back to
`aplay` (alsa-utils) if sounddevice is unavailable.
"""

import queue
import subprocess
import tempfile
import threading
import time
import wave
from pathlib import Path

import piper
from piper import PiperVoice

from config import TTS_CONFIG_PATH, TTS_MODEL_PATH

_MODEL_URL = "https://huggingface.co/rhasspy/piper-voices"


class PiperTTS:
    def __init__(self, model_path=TTS_MODEL_PATH, config_path=TTS_CONFIG_PATH):
        model_path = Path(model_path)
        if not model_path.is_file() and model_path.suffix != ".onnx":
            stem_candidate = Path(str(model_path) + ".onnx")
            if stem_candidate.is_file():
                model_path = stem_candidate
        if config_path is None:
            if model_path.suffix == ".onnx":
                config_path = Path(str(model_path) + ".json")
            else:
                config_path = Path(str(model_path) + ".onnx.json")
        config_path = Path(config_path)

        missing = [p for p in (model_path, config_path) if not p.is_file()]
        if missing:
            paths = ", ".join(str(p) for p in missing)
            raise FileNotFoundError(
                f"Piper model files not found: {paths}. "
                f"Download a Persian (fa) voice from {_MODEL_URL} and "
                f"place the .onnx and .onnx.json files in models/tts/."
            )

        self.model_path = model_path
        self.config_path = config_path
        self.sample_rate = None

        self.voice = PiperVoice.load(str(model_path), str(config_path))
        self.sample_rate = self.voice.config.sample_rate

        self._queue = queue.Queue()
        self._stop = threading.Event()
        self._thread = None

    def _synthesize_bytes(self, text: str) -> bytes:
        chunks = []
        for chunk in self.voice.synthesize(text):
            chunks.append(chunk.audio_int16_bytes)
        return b"".join(chunks)

    def _play(self, audio: bytes):
        if not audio:
            return
        try:
            import numpy as np
            import sounddevice as sd

            arr = np.frombuffer(audio, dtype=np.int16).astype("int16")
            sd.play(arr, samplerate=self.sample_rate)
            sd.wait()
        except Exception:
            self._play_aplay(audio)

    def _play_aplay(self, audio: bytes):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            with wave.open(f, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(self.sample_rate)
                w.writeframes(audio)
            subprocess.run(["aplay", "-q", f.name], check=True)
        try:
            Path(f.name).unlink(missing_ok=True)
        except OSError:
            pass

    def _worker(self):
        while not self._stop.is_set():
            try:
                text = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if text is None:
                continue
            try:
                self._play(self._synthesize_bytes(text))
            except Exception as exc:
                print(f"[tts] error: {exc}", flush=True)

    def _ensure_worker(self):
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(
                target=self._worker, name="piper-tts", daemon=True
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
        self._play(self._synthesize_bytes(text))

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

    text = "سلام، من دستیار صوتی شما هستم"
    print(f"Speaking: {text}")
    tts.speak_blocking(text)
    tts.close()