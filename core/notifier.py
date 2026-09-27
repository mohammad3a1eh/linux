"""GNOME desktop notifier via `notify-send` (preferred) or `notify2`."""

import logging
import shutil
import subprocess

_LOG = logging.getLogger(__name__)

_NOTIFY_AVAILABLE = shutil.which("notify-send") is not None
_NOTIFY_CHECKED = False


_TIMEOUT_MS = "5000"


def notify(title: str, body: str, urgency: str = "normal") -> None:
    """Send a GNOME desktop notification. Falls back to stderr on headless."""
    if _NOTIFY_AVAILABLE:
        try:
            subprocess.run(
                ["notify-send", "-t", _TIMEOUT_MS, "-u", urgency, title, body],
                check=False,
                timeout=3,
            )
            return
        except Exception as exc:
            _LOG.debug("notify-send failed: %s", exc)

    print(f"[notify {urgency}] {title}: {body}", flush=True)
