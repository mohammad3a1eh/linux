"""Report the current date and time on the host machine."""

import platform
from datetime import datetime

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_time",
        "description": (
            "Get the current local date, time, and hostname of the host machine. "
            "Useful when the user asks what time it is, the date, today's "
            "date, or the day of the week."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


def execute(**kwargs) -> str:
    now = datetime.now()
    return f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')} ({platform.node()})"


if __name__ == "__main__":
    print(execute())