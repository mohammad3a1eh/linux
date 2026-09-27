import subprocess

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "media_control",
        "description": "Control media playback (music/video) on the system. Use for play, pause, next track, or previous track. If the user asks to skip multiple tracks, set the count.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["play", "pause", "play-pause", "next", "previous"],
                    "description": "The playback action to perform.",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of times to perform the action (e.g., 2 for 'skip 2 tracks'). Default is 1.",
                    "default": 1
                }
            },
            "required": ["action"],
        },
    },
}


def execute(**kwargs) -> str:
    action = kwargs.get("action")
    count = kwargs.get("count", 1)

    if not action:
        return "Error: action is required."

    if count < 1:
        count = 1

    try:
        for _ in range(count):
            subprocess.run(["playerctl", action], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if count > 1:
            return f"Successfully executed '{action}' {count} times."
        return f"Successfully executed '{action}'."
    except FileNotFoundError:
        return "Error: 'playerctl' is not installed. Please run 'sudo apt install playerctl'."
    except subprocess.CalledProcessError:
        return "Error: Could not control media. No active media player found."