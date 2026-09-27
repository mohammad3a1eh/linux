import platform

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_system_info",
        "description": "Get CPU usage, RAM usage, and OS version of the host machine. Use when user asks about system resources, CPU, memory, RAM, or OS/distro info.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


def execute(**kwargs) -> str:
    import psutil

    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    os_info = f"{platform.system()} {platform.release()} ({platform.version()})"
    return f"CPU: {cpu}%  RAM: {ram}%  OS: {os_info}"
