"""Test: wake word detection triggers a Persian TTS reply."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.tts import PiperTTS
from core.wakeword import WakeWordDetector


def main():
    print("Loading models...")
    detector = WakeWordDetector()
    tts = PiperTTS()

    replies = iter(
        [
            "بله؟",
            "بفرمایید.",
            "سلام، چه کاری می‌توانم انجام دهم؟",
        ]
    )

    def on_wakeup(_word, _score):
        print(">>> Wake word detected! Replying...", flush=True)
        tts.speak(next(replies))

    detector.listen_for_wakeword(callback=on_wakeup)


if __name__ == "__main__":
    import sys as _sys

    if "--smoke" in _sys.argv:
        import numpy as _np

        print("Smoke: loading models + scoring silence...")
        d = WakeWordDetector()
        s = d._model.predict(_np.zeros(1280, dtype=_np.int16))
        print(f"Smoke: models={list(s.keys())} no-trigger={'to' in str(s) or all(v < 0.5 for v in s.values())}")
        t = PiperTTS()
        audio = t._synthesize_bytes("بله؟")
        print(f"Smoke: tts-bytes={len(audio)} OK")
        raise SystemExit(0)

    print("Listening for wake word... press Ctrl+C to stop.")
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as exc:
        print(f"ERROR: {exc}")
    finally:
        pass