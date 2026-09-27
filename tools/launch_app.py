import os
import subprocess
import shutil

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "launch_app",
        "description": (
            "CRITICAL: DO NOT guess the app name. You MUST NOT use this tool "
            "unless you have ALREADY used the `search_installed_apps` tool in this conversation. "
            "STEP 1: Use `search_installed_apps` to find the exact '.desktop' file name. "
            "STEP 2: Pass that exact '.desktop' filename to this tool to launch it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "The exact .desktop filename returned by search_installed_apps (e.g., 'firefox.desktop'). DO NOT pass generic names.",
                }
            },
            "required": ["app_name"],
        },
    },
}
# Well-known executable fallbacks when gtk-launch is unavailable.
_ALIAS: dict[str, str] = {
    "calculator": "gnome-calculator",
    "nautilus": "nautilus --new-window",
    "files": "nautilus --new-window",
    "settings": "gnome-control-center",
    "system-settings": "gnome-control-center",
    "terminal": "gnome-terminal",
}


def _try_gtk_launch(desktop_name: str) -> subprocess.Popen | None:
    if shutil.which("gtk-launch") is None:
        return None
    return subprocess.Popen(
        ["gtk-launch", desktop_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _try_executable(name: str) -> subprocess.Popen | None:
    exec_name = _ALIAS.get(name.lower(), name)
    parts = exec_name.split()
    if shutil.which(parts[0]) is None:
        return None
    return subprocess.Popen(
        parts,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def execute(**kwargs) -> str:
    app_name = (kwargs.get("app_name") or "").strip()
    if not app_name:
        return "Error: app_name is required."

    proc = _try_gtk_launch(app_name)
    if proc and proc.poll() is None:
        return f"Launched '{app_name}' via gtk-launch."

    proc = _try_executable(app_name)
    if proc and proc.poll() is None:
        return f"Launched '{app_name}' via direct execution."

    return (
        f"Failed to launch '{app_name}'. "
        f"Verify it is installed or try the full executable name (e.g. 'gnome-calculator')."
    )
