import subprocess
from datetime import datetime
from pathlib import Path

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "take_screenshot",
        "description": "Capture a full-screen screenshot and save it to ~/Pictures/Screenshots/. Use when the user asks to take a screenshot or capture the screen.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

_DIR = Path.home() / "Pictures" / "Screenshots"


def execute(**kwargs) -> str:
    _DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = _DIR / f"screenshot-{ts}.png"

    # Attempt 1: gnome-screenshot (X11, XWayland fallback)
    if subprocess.run(["which", "gnome-screenshot"], capture_output=True).returncode == 0:
        result = subprocess.run(
            ["gnome-screenshot", "-f", str(dest)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and dest.exists():
            return f"Screenshot saved: {dest}"
        # gnome-screenshot may require display; fall through if it fails

    # Attempt 2: scrot (available on some setups)
    if subprocess.run(["which", "scrot"], capture_output=True).returncode == 0:
        result = subprocess.run(
            ["scrot", str(dest)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and dest.exists():
            return f"Screenshot saved: {dest}"

    # Attempt 3: Wayland via grim (Sway/wlroots — common on Debian)
    if subprocess.run(["which", "grim"], capture_output=True).returncode == 0:
        result = subprocess.run(
            ["grim", str(dest)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and dest.exists():
            return f"Screenshot saved: {dest}"

    # Attempt 4: GNOME DBus screenshot (Wayland-native)
    try:
        result = subprocess.run(
            [
                "gdbus", "call",
                "--session",
                "--dest", "org.gnome.Shell.Screenshot",
                "--object-path", "/org/gnome/Shell/Screenshot",
                "--method", "org.gnome.Shell.Screenshot.Screenshot",
                "true",  # include_cursor
                "false",  # flash
                str(dest),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if dest.exists():
            return f"Screenshot saved: {dest}"
        # Also check if the call returned a success indicator
        if result.stdout and "true" in result.stdout.lower():
            return f"Screenshot saved: {dest}"
    except Exception:
        pass

    return (
        "Screenshot failed. No supported screenshot tool found.\n"
        "Install one of: sudo apt install gnome-screenshot, sudo apt install scrot, sudo apt install grim"
    )
