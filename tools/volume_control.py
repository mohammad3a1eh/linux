import subprocess

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "volume_control",
        "description": (
            "Control the system volume. "
            "If user says 'half', set to 50. If 'max', set to 100. "
            "If user says 'increase a bit', use action='increase' with amount=10. "
            "If user says 'mute', use action='mute'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["set", "increase", "decrease", "mute", "unmute"],
                    "description": "The volume action to perform.",
                },
                "amount": {
                    "type": "integer",
                    "description": "The percentage (0-100) to set, increase, or decrease. Example: 50 for half volume.",
                }
            },
            "required": ["action"],
        },
    },
}


def execute(**kwargs) -> str:
    action = kwargs.get("action")
    amount = kwargs.get("amount")

    if not action:
        return "Error: action is required."

    command = []

    if action == "mute":
        command = ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"]
    elif action == "unmute":
        command = ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"]
    else:
        # اگر amount خالی بود، پیش‌فرض ۱۰ درصد در نظر می‌گیریم
        val = amount if amount is not None else 10

        if action == "set":
            # محدود کردن بین ۰ تا ۱۰۰
            val = max(0, min(100, val))
            command = ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{val}%"]
        elif action == "increase":
            command = ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"+{val}%"]
        elif action == "decrease":
            command = ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"-{val}%"]

    try:
        if action in ["set", "increase", "decrease"]:
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], check=False)

        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if amount is not None:
            return f"Volume {action} to/by {amount}%."
        return f"Volume {action} executed."
    except FileNotFoundError:
        return "Error: 'pactl' is not installed."
    except subprocess.CalledProcessError:
        return "Error: Failed to change volume. PulseAudio/PipeWire might not be running properly."