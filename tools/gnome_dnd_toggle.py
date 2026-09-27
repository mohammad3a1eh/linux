import subprocess
import shutil

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "gnome_dnd_toggle",
        "description": "Toggle GNOME Do Not Disturb mode on or off. Use when the user asks to enable/disable DND, quiet hours, or to mute desktop notifications.",
        "parameters": {
            "type": "object",
            "properties": {
                "enable": {
                    "type": "boolean",
                    "description": "True to turn ON Do Not Disturb (mute notifications). False to turn it OFF (allow notifications).",
                }
            },
            "required": ["enable"],
        },
    },
}


def _gsettings_available() -> bool:
    return shutil.which("gsettings") is not None


def execute(**kwargs) -> str:
    enable_raw = kwargs.get("enable")
    if enable_raw is None:
        return "Error: 'enable' parameter is required (true/false)."
    enable = bool(enable_raw)
    state = "ON" if enable else "OFF"

    if not _gsettings_available():
        return "gsettings not available. Is GNOME installed?"

    gsettings_val = "false" if enable else "true"

    result = subprocess.run(
        [
            "gsettings", "set",
            "org.gnome.desktop.notifications",
            "show-banners",
            gsettings_val,
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )

    if result.returncode != 0:
        err = result.stderr.strip()
        return f"Failed to toggle Do Not Disturb: {err or 'unknown error'}"

    verify = subprocess.run(
        [
            "gsettings", "get",
            "org.gnome.desktop.notifications",
            "show-banners",
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )
    current = verify.stdout.strip()
    # gsettings returns gvariant strings: 'true' or 'false'
    # show-banners=false means notifications muted = DND ON
    current_state = "ON" if current.strip("'\"") == "false" else "OFF"
    return f"Do Not Disturb: {current_state} (notifications {'muted' if current_state == 'ON' else 'active'})"


if __name__ == "__main__":
    print(execute(enable=True))
    print(execute(enable=False))
