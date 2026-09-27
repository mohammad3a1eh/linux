import os
import difflib

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_installed_apps",
        "description": "MANDATORY: You MUST use this tool immediately whenever the user asks to open, launch, or find any application or software category (like 'image editor', 'browser', 'music'). DO NOT ask the user for clarification. Pass their exact keyword as the query to see what is available.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search term or category the user mentioned (e.g., 'image editor', 'browser', 'music').",
                }
            },
            "required": ["query"],
        },
    },
}


def execute(**kwargs) -> str:
    query = (kwargs.get("query") or "").strip().lower()
    if not query:
        return "Error: query is required."

    # مسیرهای استاندارد برنامه‌ها در دبیان/گنوم
    app_dirs = [
        "/usr/share/applications",
        os.path.expanduser("~/.local/share/applications"),
        "/var/lib/flatpak/exports/share/applications"
    ]

    matches = []
    query_words = query.split()

    for directory in app_dirs:
        if not os.path.exists(directory):
            continue

        for filename in os.listdir(directory):
            if not filename.endswith(".desktop"):
                continue

            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                    name = ""
                    categories = ""

                    # استخراج نام و دسته‌بندی برنامه
                    for line in content.splitlines():
                        if line.startswith("Name=") and not name:
                            name = line.split("=", 1)[1].strip()
                        elif line.startswith("Categories=") and not categories:
                            categories = line.split("=", 1)[1].strip()

                    # متن کامل برای جستجو
                    search_text = f"{filename} {name} {categories}".lower()
                    # شکستن متن به کلمات مجزا برای بررسی غلط املایی
                    text_words = search_text.replace("-", " ").replace(";", " ").replace(".", " ").split()

                    is_match = False

                    # بررسی اول: آیا کل عبارت دقیقاً در متن هست؟
                    if query in search_text:
                        is_match = True
                    else:
                        # بررسی دوم: سیستم ضد غلط املایی (Fuzzy Search)
                        # اگر هر کدام از کلمات کوئری، شباهت ۷۰ درصدی با کلمات برنامه داشت
                        for qw in query_words:
                            if difflib.get_close_matches(qw, text_words, n=1, cutoff=0.7):
                                is_match = True
                                break

                    if is_match:
                        matches.append(f"- App Name: '{name}' | Desktop File: '{filename}'")

                        # محدود کردن نتایج به ۱۵ مورد
                        if len(matches) >= 15:
                            break
            except Exception:
                continue

        if len(matches) >= 15:
            break

    if not matches:
        return f"No apps found matching '{query}'."

    return f"Found {len(matches)} apps. Pass the exact 'Desktop File' name to the launch_app tool:\n" + "\n".join(
        matches)