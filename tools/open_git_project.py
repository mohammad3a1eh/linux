import os
import subprocess
import shutil

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "open_git_project",
        "description": (
            "Searches the user's system for Git repositories and opens the folder of the requested project. "
            "Use this tool when the user asks to open a specific programming project, repository, or source code."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "The name of the project or repository to find and open (e.g., 'payload', 'my-website').",
                }
            },
            "required": ["project_name"],
        },
    },
}


def _get_all_git_projects(max_depth: int = 5) -> dict[str, str]:
    """
    از دستور find لینوکس استفاده می‌کند تا خیلی سریع تمام پوشه‌های .git را در پوشه home پیدا کند.
    استفاده از maxdepth باعث می‌شود کل هارد اسکن نشود و سرعت بالا بماند.
    """
    projects = {}
    try:
        # جستجو در پوشه Home کاربر (~) تا عمق ۵ پوشه
        cmd = f'find ~ -maxdepth {max_depth} -type d -name ".git" 2>/dev/null'

        # اجرای دستور و گرفتن خروجی
        output = subprocess.check_output(cmd, shell=True, text=True).strip()

        if not output:
            return projects

        for git_dir in output.split('\n'):
            if git_dir.endswith('.git'):
                # گرفتن آدرس پوشه اصلی پروژه (بدون /.git)
                project_dir = os.path.dirname(git_dir)
                # گرفتن نام پوشه به عنوان نام پروژه
                project_name = os.path.basename(project_dir).lower()
                projects[project_name] = project_dir
    except subprocess.CalledProcessError:
        pass

    return projects


def execute(**kwargs) -> str:
    project_name = (kwargs.get("project_name") or "").strip().lower()
    if not project_name:
        return "Error: project_name is required."

    # مرحله اول: گرفتن لیست تمام پروژه‌های گیت سیستم
    all_projects = _get_all_git_projects()

    if not all_projects:
        return "No Git projects found in the home directory."

    best_match_path = None

    # مرحله دوم: پیدا کردن پروژه مورد نظر در لیست
    # ابتدا بررسی می‌کنیم آیا نام دقیق پروژه وجود دارد؟
    if project_name in all_projects:
        best_match_path = all_projects[project_name]
    else:
        # اگر نام دقیق نبود، بررسی می‌کنیم آیا کلمه‌ای که کاربر گفته بخشی از نام یک پروژه هست؟
        for name, path in all_projects.items():
            if project_name in name or name in project_name:
                best_match_path = path
                break

    # مرحله سوم: باز کردن پروژه پیدا شده
    if best_match_path:
        # می‌توانید به جای xdg-open از "code" استفاده کنید تا مستقیم در VS Code باز شود
        # xdg-open پوشه را در فایل‌منیجر پیش‌فرض (مثل Nautilus) باز می‌کند
        opener = shutil.which("xdg-open") or shutil.which("nautilus")

        if opener:
            subprocess.Popen(
                [opener, best_match_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return f"Project '{project_name}' found and opened successfully."
        else:
            return f"Project found at {best_match_path}, but no file manager found to open it."

    else:
        # اگر پروژه پیدا نشد، چندتا از پروژه‌های موجود را برمی‌گردانیم تا هوش مصنوعی به کاربر بگوید
        available = ", ".join(list(all_projects.keys())[:5])
        return f"Could not find project '{project_name}'. Some available projects are: {available}"