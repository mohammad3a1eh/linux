"""Keyboard-shortcut activation via a GNOME custom keybinding.

The assistant registers a global hotkey with gsettings
(org.gnome.settings-daemon.plugins.media-keys custom-keybindings).
When the user presses the hotkey the compositor runs this file as
`python shortcut.py send <socket>`. The running assistant's
ShortcutListener accepts that connection and calls its on_trigger
callback, so the idle loop exits the wake-word wait and moves straight
to the LISTENING phase. Works on GNOME Wayland and X11.

Stdlib-only (socket + threading) — no new pip packages.
"""

import logging
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import threading
from pathlib import Path

_LOG = logging.getLogger(__name__)

_SOCKET_NAME = "voice-assistant-activate.sock"
_MEDIA_KEYS = "org.gnome.settings-daemon.plugins.media-keys"
_KEYBINDINGS_KEY = "custom-keybindings"
_BINDING_PATH = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/voice-assistant/"
_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
_SCHEMA_PATH = f"{_SCHEMA}:{_BINDING_PATH}"


def shortcut_socket_path() -> str:
    base = os.environ.get("XDG_RUNTIME_DIR") or f"/tmp/run-{os.getuid()}"
    return os.path.join(base, _SOCKET_NAME)


class ShortcutListener:
    """Unix-socket server that trips when the GNOME hotkey fires it."""

    def __init__(self, socket_path=None, on_trigger=None):
        self.socket_path = socket_path or shortcut_socket_path()
        self.on_trigger = on_trigger
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._serve, name="shortcut-listener", daemon=True
        )
        self._thread.start()

    def _serve(self):
        path = self.socket_path
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except OSError:
            pass
        try:
            os.unlink(path)
        except OSError:
            pass

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            server.bind(path)
            server.listen(4)
            server.settimeout(0.5)
            _LOG.info("Shortcut listener on %s", path)
            while not self._stop.is_set():
                try:
                    conn, _ = server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                with conn:
                    try:
                        conn.recv(16)
                    except OSError:
                        pass
                if self.on_trigger is not None:
                    self.on_trigger()
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
            server.close()

    def stop(self):
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1.0)


def _send(socket_path) -> bool:
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            client.settimeout(2.0)
            client.connect(socket_path)
            client.sendall(b"\n")
        finally:
            client.close()
        return True
    except OSError:
        return False


def _qc(token) -> str:
    return shlex.quote(str(token))


def register_shortcut(
    binding=None,
    socket_path=None,
    display_name="Voice Assistant",
) -> str:
    """Install (idempotently) the GNOME custom keybinding. Returns a status string."""
    socket_path = socket_path or shortcut_socket_path()
    if binding is None:
        from config import ACTIVATION_SHORTCUT
        binding = ACTIVATION_SHORTCUT
    gsettings = shutil.which("gsettings")
    if gsettings is None:
        return "gsettings unavailable - keyboard shortcut not registered"

    helper = (
        f"{_qc(sys.executable)} {_qc(str(Path(__file__).resolve()))} "
        f"send {_qc(socket_path)}"
    )
    if not Path(sys.executable).exists():
        helper = (
            f"{_qc(shutil.which('python3') or '/usr/bin/python3')} "
            f"{_qc(str(Path(__file__).resolve()))} send {_qc(socket_path)}"
        )

    def set_key(key, value):
        result = subprocess.run(
            [gsettings, "set", _SCHEMA_PATH, key, value],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"gsettings set {key} failed: {result.stderr.strip()}")
        return result

    try:
        cur = subprocess.run(
            [gsettings, "get", _MEDIA_KEYS, _KEYBINDINGS_KEY],
            capture_output=True,
            text=True,
        ).stdout
        paths = re.findall(r"'([^']+)'", cur or "") if cur else []
        if _BINDING_PATH not in paths:
            paths.append(_BINDING_PATH)
            list_repr = "[" + ", ".join(repr(p) for p in paths) + "]"
            subprocess.run(
                [gsettings, "set", _MEDIA_KEYS, _KEYBINDINGS_KEY, list_repr],
                check=True,
                capture_output=True,
                text=True,
            )
        set_key("name", display_name)
        set_key("command", helper)
        set_key("binding", binding)
    except Exception as exc:
        return f"Shortcut registration failed: {exc}"

    return f"Keyboard shortcut registered: {binding}"


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "send":
        target = sys.argv[2] if len(sys.argv) > 2 else shortcut_socket_path()
        sys.exit(0 if _send(target) else 1)
    print(f"Socket: {shortcut_socket_path()}")