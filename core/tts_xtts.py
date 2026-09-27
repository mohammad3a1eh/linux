"""Offline Text-to-Speech using XTTSv2 (Coqui TTS) with Voice Cloning.

Synthesis runs in a background worker thread so `speak()` never blocks the
GTK main loop. Audio is played with sounddevice (PortAudio), falling back to
`aplay` (alsa-utils) if sounddevice is unavailable.
"""

import queue
import subprocess
import tempfile
import threading
import wave
from pathlib import Path
import numpy as np

import torch
from TTS.api import TTS


class XTTSv2Engine:
    def __init__(self, ref_audio_path="models/tts/female_ref.wav", language="en"):
        # بررسی وجود فایل صوتی مرجع (برای کلون کردن صدای دختر)
        self.ref_audio = Path(ref_audio_path)
        if not self.ref_audio.is_file():
            raise FileNotFoundError(
                f"Reference audio not found: {self.ref_audio}. "
                f"Please place a 5-10 second clean .wav file of a female voice in this path."
            )

        self.language = language

        # تشخیص خودکار کارت گرافیک (برای سرعت بالا) یا استفاده از CPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[TTS] Loading XTTSv2 model on {self.device.upper()}... This might take a moment.")

        # لود کردن مدل XTTSv2 (در اولین اجرا مدل را دانلود می‌کند ~2GB)
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
        print("[TTS] Model loaded successfully!")

        # فرکانس استاندارد خروجی XTTSv2
        self.sample_rate = 24000

        self._queue = queue.Queue()
        self._stop = threading.Event()
        self._thread = None

    def _synthesize_bytes(self, text: str) -> bytes:
        """تبدیل متن به صدای خام (آرایه اعداد) و سپس به بایت"""
        # تولید صدا با استفاده از فایل مرجع
        wav_data = self.tts.tts(text=text, speaker_wav=str(self.ref_audio), language=self.language)

        # XTTS خروجی را به صورت لیستی از Float برمی‌گرداند. باید به 16-bit PCM تبدیل شود
        wav_array = np.array(wav_data)
        audio_int16 = (wav_array * 32767).astype(np.int16)

        return audio_int16.tobytes()

    def _play(self, audio: bytes):
        if not audio:
            return
        try:
            import sounddevice as sd
            arr = np.frombuffer(audio, dtype=np.int16)
            sd.play(arr, samplerate=self.sample_rate)
            sd.wait()
        except Exception as e:
            print(f"[TTS] sounddevice failed ({e}), falling back to aplay...")
            self._play_aplay(audio)

    def _play_aplay(self, audio: bytes):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            with wave.open(f, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)  # 16-bit
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
                # اول تبدیل متن به بایت صوتی، بعد پخش
                audio_bytes = _synthesize_bytes(text)
                self._play(audio_bytes)
            except Exception as exc:
                print(f"[TTS] error during synthesis/playback: {exc}", flush=True)

    def _ensure_worker(self):
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(
                target=self._worker, name="xtts-worker", daemon=True
            )
            self._thread.start()

    def speak(self, text: str):
        """اضافه کردن متن به صف برای پردازش در بک‌گراند (بدون فریز کردن برنامه)"""
        if not text.strip():
            return
        self._ensure_worker()
        self._queue.put(text)

    def speak_blocking(self, text: str):
        """صبر می‌کند تا تولید صدا تمام شود و بلافاصله پخش می‌کند"""
        self._play(self._synthesize_bytes(text))

    def stop(self):
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
        # نکته: حتما یک فایل صدای دخترانه در مسیر زیر قرار بده
        tts = XTTSv2Engine(ref_audio_path="models/tts/female_ref.wav", language="en")
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)

    text = "Oh, hello there! I am your new voice assistant. How are you doing today?"
    print(f"Speaking: {text}")
    tts.speak_blocking(text)
    tts.close()