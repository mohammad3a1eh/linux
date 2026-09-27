import shutil

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "disk_storage",
        "description": "Return disk usage for the root partition: total, used, and free space in GB. Use when the user asks about disk space or storage.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

_BYTES_PER_GB = 1 << 30


def execute(**kwargs) -> str:
    try:
        total, used, free = shutil.disk_usage("/")
        total_gb = total / _BYTES_PER_GB
        used_gb = used / _BYTES_PER_GB
        free_gb = free / _BYTES_PER_GB
        used_pct = (used / total) * 100
        return (
            f"Disk usage (/): {used_gb:.1f} GB / {total_gb:.1f} GB "
            f"({used_pct:.1f}% used)  |  Free: {free_gb:.1f} GB"
        )
    except Exception as exc:
        return f"Failed to read disk usage: {exc}"
