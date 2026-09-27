"""Headless voice assistant daemon with GNOME desktop notifications."""

import logging
import threading
import time

from core.llm import LocalLLM
from core.notifier import notify
from core.shortcut import ShortcutListener, register_shortcut, shortcut_socket_path
from core.stt import VoskSTT
from core.tts import PiperTTS
from core.wakeword import WakeWordDetector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def main():
    detector = None
    stt = None
    tts = None

    try:
        logging.info("Loading models...")
        detector = WakeWordDetector()
        stt = VoskSTT()
        tts = PiperTTS()
        llm = LocalLLM()
    except Exception as exc:
        logging.error("Failed to load one or more modules: %s", exc)
        # notify("Voice Assistant", f"Model load error: {exc}", "critical")
        return

    logging.info("All modules loaded — entering main loop")
    shortcut_sock = shortcut_socket_path()
    shortcut_pending = threading.Event()
    listener = ShortcutListener(
        socket_path=shortcut_sock,
        on_trigger=lambda: (
            shortcut_pending.set(),
            detector.stop(),
        ),
    )
    listener.start()
    try:
        logging.info(register_shortcut(socket_path=shortcut_sock))
    except Exception as exc:
        logging.warning("Shortcut registration skipped: %s", exc)
    # notify("Voice Assistant", "Ready. Say the wake word...", "normal")

    try:
        while True:
            # ---- IDLE: listen for wake word OR keyboard shortcut ----
            detector.flush()
            shortcut_pending.clear()
            activated = _wait_for_activation(detector, shortcut_pending)
            if activated is None:
                continue
            if activated == "shortcut":
                logging.info("Activated by keyboard shortcut!")
            else:
                logging.info("Wake word detected!")
            _beep()
            # notify("Voice Assistant", "Yes? I'm listening...")

            # ---- LISTENING ----
            logging.info("Listening for user voice...")
            user_text = ""
            try:
                gen = stt.listen(timeout_seconds=10)
                try:
                    user_text = next(gen)
                except StopIteration:
                    user_text = stt.finalize()
                finally:
                    close = getattr(gen, "close", None)
                    if close:
                        close()
            except Exception as exc:
                logging.error("STT error: %s", exc)
                continue

            if not user_text:
                logging.info("STT Timeout: No voice detected.")
                # intentionally no notification — silence is expected
                continue

            # notify("You said:", user_text)
            logging.info("Heard: %s", user_text)

            # ---- PROCESSING ----
            # notify("Voice Assistant", "Processing...")
            logging.info("Sending request to LLM...")
            try:
                context = _get_context()
                reply = llm.generate_response(user_text, system_data=context)
            except Exception as exc:
                logging.error("LLM error: %s", exc)
                continue
            if not reply:
                continue
            notify("Voice Assistant", reply)
            logging.info("LLM Response: %s", reply)

            # ---- SPEAKING ----
            logging.info("Generating and playing TTS audio...")
            try:
                tts.speak_blocking(reply)
            except Exception as exc:
                logging.error("TTS error: %s", exc)

            # ---- SELF-TRIGGER GUARD: let echoes fade, flush mic ----
            time.sleep(0.5)
            detector.flush()

    except KeyboardInterrupt:
        logging.info("Ctrl+C received — shutting down...")
    finally:
        listener.stop()
        for mod in (detector, stt, tts):
            if mod is not None:
                try:
                    mod.stop()
                except Exception:
                    pass
        # notify("Voice Assistant", "Shutting down.", "low")
        logging.info("Shutdown complete.")


def _wait_for_activation(detector, shortcut_pending) -> str | None:
    """Block until wake word or keyboard shortcut. Returns source or None."""
    while True:
        gen = detector.listen_for_wakeword()
        try:
            try:
                next(gen)
                return "wakeword"
            except StopIteration:
                pass
        finally:
            close = getattr(gen, "close", None)
            if close:
                close()
        if shortcut_pending.is_set():
            shortcut_pending.clear()
            return "shortcut"
        time.sleep(0.1)


def _beep():
    try:
        import numpy as np
        import sounddevice as sd
        sr = 16000
        dur = 0.15
        t = np.linspace(0, dur, int(sr * dur), False)
        tone = (np.sin(2 * np.pi * 880 * t) * 0.4 * 32767).astype("int16")
        sd.play(tone, samplerate=sr)
        sd.wait()
    except Exception:
        pass


def _get_context() -> str | None:
    try:
        import psutil

        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        return f"CPU: {cpu}%  RAM: {mem}%"
    except Exception:
        return None


if __name__ == "__main__":
    main()