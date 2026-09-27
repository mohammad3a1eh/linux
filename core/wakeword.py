"""Offline hotword detection using openWakeWord + sounddevice."""

import queue
import threading
from pathlib import Path

import numpy as np
from openwakeword.model import Model

SAMPLE_RATE = 16000
_CHANNELS = 1
_CHUNK_SAMPLES = 1280
_COOLDOWN_SEC = 1.5
_PREROLL_SEC = 1.0


from config import WAKEWORD_MODEL_PATH

class WakeWordDetector:
    _DEFAULT_MODEL = WAKEWORD_MODEL_PATH

    def __init__(
        self,
        model_path: str = None,
        threshold: float = 0.1,
        cooldown_sec: float = _COOLDOWN_SEC,
    ):
        wakeword_models = Path(model_path or self._DEFAULT_MODEL)

        if not wakeword_models.is_file():
            raise FileNotFoundError(
                f"Wake word model not found at {wakeword_models}. "
                "Place a .onnx model in models/wakeword/ or pass its path."
            )

        models = [str(wakeword_models)]

        self._model = Model(wakeword_models=models, inference_framework="onnx")
        self.threshold = threshold
        self.cooldown_sec = cooldown_sec
        self.model_names = list(self._model.models.keys())

        self._frame_q = queue.Queue()
        self._stop = threading.Event()
        self._stream = None
        self._cooldown_until = 0.0

    def _audio_callback(self, indata, _frames, _time, status):
        if status:
            print(f"[wakeword] audio status: {status}", flush=True)
        self._frame_q.put(bytes(indata))

    def _start_stream(self):
        try:
            import sounddevice as sd
        except OSError as exc:
            raise OSError(
                "sounddevice needs PortAudio: install libportaudio2 "
                "(sudo apt install libportaudio2)"
            ) from exc

        self.stop()
        self.flush()
        self._stop.clear()
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=_CHANNELS,
            dtype="int16",
            blocksize=_CHUNK_SAMPLES,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._discard_preroll()

    def _discard_preroll(self):
        """Read and throw away ~1s of audio trapped in the OS mic buffer."""
        chunks = int((_PREROLL_SEC * SAMPLE_RATE) / _CHUNK_SAMPLES)
        for _ in range(chunks):
            try:
                self._frame_q.get(timeout=1.0)
            except queue.Empty:
                break

    def flush(self):
        """Drop queued frames and reset the openWakeWord model state."""
        while True:
            try:
                self._frame_q.get_nowait()
            except queue.Empty:
                break
        try:
            self._model.reset()
        except Exception:
            pass

    def _pending_frames(self) -> np.ndarray:
        """Drain queue into one int16 numpy array of accumulated samples."""
        parts = []
        while True:
            try:
                parts.append(self._frame_q.get_nowait())
            except queue.Empty:
                break
        if not parts:
            return None
        return np.frombuffer(b"".join(parts), dtype=np.int16)

    def listen_for_wakeword(self, callback=None):
        """Yield True (or call callback) once per wake-word utterance."""
        import time

        self._start_stream()
        try:
            while not self._stop.is_set():
                try:
                    frame = self._frame_q.get(timeout=0.1)
                except queue.Empty:
                    continue

                audio = np.frombuffer(frame, dtype=np.int16)
                scores = self._model.predict(audio)
                max_score = max(scores.values(), default=0.0)

                if max_score >= self.threshold:
                    now = time.monotonic()
                    if now >= self._cooldown_until:
                        self._cooldown_until = now + self.cooldown_sec
                        word = max(scores, key=scores.get)
                        print(
                            f"[wakeword] detected '{word}' (score={scores[word]:.2f})",
                            flush=True,
                        )
                        self.stop()
                        self.flush()
                        if callback is not None:
                            callback(word, scores[word])
                        else:
                            yield True
        finally:
            self.stop()

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
        detector = WakeWordDetector()
    except Exception as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)

    print("Listening for wake word ('Hey Linux')... press Ctrl+C to stop.")
    try:
        for _ in detector.listen_for_wakeword():
            print("Wake word detected!")
    except KeyboardInterrupt:
        pass
    finally:
        detector.close()