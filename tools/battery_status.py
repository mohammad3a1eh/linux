TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "battery_status",
        "description": "Return current battery percentage and charging status of the laptop. Use when user asks about battery level or power status.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


def _read_sysfs(key: str, default: str = "") -> str:
    try:
        with open(f"/sys/class/power_supply/BAT0/{key}") as f:
            return f.read().strip()
    except Exception:
        return default


def execute(**kwargs) -> str:
    try:
        import psutil

        bat = psutil.sensors_battery()
        if bat is None:
            return "No battery detected on this system."
        pct = bat.percent
        plugged = bat.power_plugged
        if plugged:
            status = "Charging" if pct < 100 else "Full"
        else:
            status = "Discharging"
        secs = bat.secsleft
        if secs > 0 and secs < 36000:
            hrs, rem = divmod(int(secs), 3600)
            mins = rem // 60
            return f"Battery: {pct:.0f}%  Status: {status}  Time remaining: {hrs}h {mins}m"
        return f"Battery: {pct:.0f}%  Status: {status}"
    except Exception:
        pass

    pct_raw = _read_sysfs("capacity")
    status_raw = _read_sysfs("status")
    if not pct_raw:
        return "No battery detected on this system."
    pct = int(pct_raw)
    status = status_raw.replace("Discharging", "Discharging").replace("Charging", "Charging").replace("Full", "Full")
    if not status:
        status = "Unknown"
    return f"Battery: {pct}%  Status: {status}"


if __name__ == "__main__":
    print(execute())
