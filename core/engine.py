"""Pipeline orchestrator — runs wake→STT→LLM→TTS on a dedicated QThread."""

import logging
import threading
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

from PySide6.QtCore import QThread, Signal

from core.llm import LocalLLM
from core.shortcut import ShortcutListener, register_shortcut, shortcut_socket_path
from core.stt import VoskSTT
from core.tts import PiperTTS
from core.wakeword import WakeWordDetector
from gui.signals import signals

_LOG = logging.getLogger(__name__)


class AssistantWorker(QThread):
    finished_cycle = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shutdown = threading.Event()
        self._detector = None
        self._stt = None
        self._tts = None
        self._shortcut_pending = threading.Event()
        self._shortcut_listener = None

    # ------------------------------------------------------------------ #
    #  Graceful shutdown — call from the main thread on window close      #
    # ------------------------------------------------------------------ #
    def shutdown(self):
        self._shutdown.set()
        if self._shortcut_listener is not None:
            try:
                self._shortcut_listener.stop()
            except Exception:
                pass
        for mod in (self._detector, self._stt, self._tts):
            if mod is not None:
                try:
                    mod.stop()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    #  Main loop                                                         #
    # ------------------------------------------------------------------ #
    def run(self):
        try:
            self._detector = WakeWordDetector()
            self._stt = VoskSTT()
            self._tts = PiperTTS()
            llm = LocalLLM()
        except Exception as exc:
            _LOG.error("Failed to load one or more modules: %s", exc)
            signals.text_updated.emit(f"Model load error: {exc}")
            return

        _LOG.info("All modules loaded — entering main loop")

        shortcut_sock = shortcut_socket_path()
        self._shortcut_pending.clear()
        self._shortcut_listener = ShortcutListener(
            socket_path=shortcut_sock,
            on_trigger=lambda: (
                self._shortcut_pending.set(),
                self._detector.stop() if self._detector is not None else None,
            ),
        )
        self._shortcut_listener.start()
        try:
            _LOG.info(register_shortcut(socket_path=shortcut_sock))
        except Exception as exc:
            _LOG.warning("Shortcut registration skipped: %s", exc)

        while not self._shutdown.is_set():
            try:
                # ---- IDLE ----
                signals.state_changed.emit("idle")

                self._detector.flush()
                self._shortcut_pending.clear()
                activated = self._wait_for_activation()
                if activated == "wakeword":
                    logging.info("Wake word detected!")
                elif activated == "shortcut":
                    logging.info("Activated by keyboard shortcut!")
                else:
                    if self._shutdown.is_set():
                        break
                    continue
                self._beep()

                # ---- LISTENING ----
                signals.state_changed.emit("listening")
                logging.info("Listening for user voice...")
                try:
                    user_text = self._listen_command(timeout_seconds=10)
                except Exception as e:
                    logging.error(f"Error in pipeline: {e}")
                    continue
                if not user_text:
                    logging.info("STT Timeout: No voice detected.")
                    signals.state_changed.emit("idle")
                    continue
                signals.text_updated.emit(user_text)
                logging.info(f"Heard: {user_text}")

                # ---- PROCESSING ----
                signals.state_changed.emit("processing")
                logging.info("Sending request to LLM...")
                try:
                    context = self._get_context()
                    reply = self._generate(llm, user_text, context)
                except Exception as e:
                    logging.error(f"Error in pipeline: {e}")
                    continue
                if not reply:
                    continue
                logging.info(f"LLM Response: {reply}")

                # ---- SPEAKING ----
                signals.state_changed.emit("speaking")
                logging.info("Generating and playing TTS audio...")
                try:
                    self._speak(reply)
                except Exception as e:
                    logging.error(f"Error in pipeline: {e}")

                # ---- SELF-TRIGGER GUARD ----
                # Let room echoes fade, then flush stale mic audio so the
                # next idle loop starts from a clean buffer.
                if not self._shutdown.is_set():
                    time.sleep(0.5)
                    self._detector.flush()
            except Exception as e:
                logging.error(f"Error in pipeline: {e}")
                continue

        self.finished_cycle.emit("stopped")
        if self._shortcut_listener is not None:
            try:
                self._shortcut_listener.stop()
            except Exception:
                pass
        _LOG.info("Worker loop exited")

    # ------------------------------------------------------------------ #
    #  Stage helpers                                                      #
    # ------------------------------------------------------------------ #
    def _wait_for_activation(self) -> str | None:
        """Block until wake word or shortcut fires. Returns source or None."""
        while True:
            gen = self._detector.listen_for_wakeword()
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
            if self._shortcut_pending.is_set():
                self._shortcut_pending.clear()
                return "shortcut"
            if self._shutdown.is_set():
                return None
            time.sleep(0.1)

    def _listen_command(self, timeout_seconds: float = 5.0) -> str:
        gen = self._stt.listen(timeout_seconds=timeout_seconds)
        try:
            text = next(gen)
        except StopIteration:
            text = self._stt.finalize()
        finally:
            close = getattr(gen, "close", None)
            if close:
                close()
            self._stt.stop()
        return text.strip() if text else ""

    def _get_context(self) -> str | None:
        try:
            import psutil

            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent
            return f"CPU: {cpu}%  RAM: {mem}%"
        except Exception:
            return None

    def _generate(self, llm: LocalLLM, user_text: str, context: str | None) -> str:
        try:
            return llm.generate_response(user_text, system_data=context)
        except Exception as exc:
            _LOG.error("LLM error: %s", exc)
            return "متأسفم، مشکلی پیش آمد."

    def _beep(self):
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

    def _speak(self, text: str):
        self._tts.speak_blocking(text)
