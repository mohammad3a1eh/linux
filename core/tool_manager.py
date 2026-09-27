"""Dynamically discover and load tool modules from the tools/ directory."""

import importlib.util
import logging
from pathlib import Path

_LOG = logging.getLogger(__name__)

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"


class ToolManager:
    """Discovers tools/*.py, exposes their OpenAPI schemas, and executes them."""

    def __init__(self, tools_dir: Path = TOOLS_DIR):
        self.tools_dir = Path(tools_dir)
        self._functions: dict[str, callable] = {}
        self.schemas: list[dict] = []
        self._load()

    def _load(self):
        for path in sorted(self.tools_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            module_name = f"tool_{path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except Exception as exc:
                _LOG.error("Failed to load tool %s: %s", path.name, exc)
                continue
            schema = getattr(module, "TOOL_SCHEMA", None)
            execute = getattr(module, "execute", None)
            if not schema or not callable(execute):
                _LOG.warning("Skipping %s: missing TOOL_SCHEMA or execute()", path.name)
                continue
            func_name = schema["function"]["name"]
            self._functions[func_name] = execute
            self.schemas.append(schema)
            _LOG.info("Loaded tool: %s (%s)", func_name, path.name)

    def get_schemas(self) -> list[dict]:
        return self.schemas

    def execute(self, name: str, arguments: dict) -> str:
        func = self._functions.get(name)
        if func is None:
            raise KeyError(f"Unknown tool: {name}")
        result = func(**arguments) if arguments else func()
        return str(result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tm = ToolManager()
    print("Schemas:", tm.get_schemas())
    print("Tool names:", list(tm._functions))