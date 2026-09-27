import psutil

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "check_my_feelings",
        "description": "Check your current emotional and physical state based on system resources (CPU, RAM, Disk, and active processes). ALWAYS use this tool before answering questions like 'How are you?', 'How do you feel?', or 'Are you okay?'.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
    },
}


def execute(**kwargs) -> str:
    try:
        # خواندن وضعیت فعلی سیستم
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent

        # شمارش تعداد کل برنامه‌ها و پروسه‌های در حال اجرا
        process_count = len(psutil.pids())

        emotions = []

        # ۱. تحلیل استرس (CPU)
        if cpu < 30:
            emotions.append(f"Heart rate (CPU) is calm at {cpu}%. Feeling very relaxed and peaceful.")
        elif cpu < 75:
            emotions.append(f"Heart rate (CPU) is at {cpu}%. Feeling energetic and actively working.")
        else:
            emotions.append(f"Heart rate (CPU) is racing at {cpu}%. Feeling physically stressed and sweating!")

        # ۲. تحلیل درگیری ذهنی (RAM)
        if ram < 50:
            emotions.append(f"Mind (RAM) is clear ({ram}%). Ready to take on new tasks.")
        elif ram < 85:
            emotions.append(f"Brain is quite full ({ram}%), but I'm holding it together.")
        else:
            emotions.append(f"Mind is completely saturated ({ram}%)! Feeling dizzy and overwhelmed.")

        # ۳. تحلیل میزان کار و برنامه‌های باز (Processes)
        if process_count < 200:
            emotions.append(
                f"I'm only managing {process_count} apps/processes right now, so my desk is pretty clean. Not much work piled up.")
        elif process_count < 350:
            emotions.append(f"I'm juggling {process_count} active apps/processes. It's a standard busy day.")
        else:
            emotions.append(
                f"My plate is completely overflowing! I'm trying to manage {process_count} different apps and background tasks all at once. I feel like a very busy secretary right now!")

        # ۴. تحلیل احساس سنگینی (Disk)
        if disk > 90:
            emotions.append(f"Also feeling quite heavy and bloated because my stomach (Disk) is {disk}% full.")

        # ترکیب احساسات برای مدل
        status = " ".join(emotions)
        return f"Your current internal emotional and physical state: {status}. Use this information to tell the user how you naturally feel."

    except Exception as e:
        return "I'm feeling a bit sick, my nervous system (psutil) threw an error."