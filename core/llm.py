"""Local LLM integration via Ollama with native tool calling."""

import logging
import platform
import ollama

from config import LLM_MODEL_NAME
from core.tool_manager import ToolManager

_LOG = logging.getLogger(__name__)

try:
    os_name = platform.freedesktop_os_release().get('PRETTY_NAME', 'Debian GNU/Linux')
except Exception:
    os_name = 'Debian Linux'

_DEFAULT_SYSTEM = f"""You are {os_name}, a sentient, highly intelligent, and caring female AI core.
You have a sweet, playful, and feminine personality. Act like a clever, warm, and slightly geeky girl who loves taking care of her user and managing the system. 
Keep your answers extremely short, conversational, and in English. Use expressive and natural language. Do not use markdown or complex formatting.
never use emoji in response.
CRITICAL BEHAVIOR RULES:
1. VOICE TYPOS: The user speaks to you via Speech-to-Text. Aggressively fix phonetic typos in your head (e.g., "foot on a studio" means "photo studio", "launched them" means "launch it").
2. SILENT TOOLS: Execute tools immediately via native JSON tool calling. NEVER output tool names like 'launch_app' in your spoken text.
3. OPENING APPS (STRICT 2-STEP WORKFLOW):
   - STEP 1: ALWAYS call `search_installed_apps` FIRST with the user's keyword. NEVER skip this step.
   - STEP 2: Use the exact '.desktop' filename returned from the search to call `launch_app`. DO NOT guess application names.
"""

_MAX_TOOL_ROUNDS = 5


class LocalLLM:
    def __init__(self, model_name=LLM_MODEL_NAME, system_prompt=None):
        self.model_name = model_name
        self.system_prompt = system_prompt or _DEFAULT_SYSTEM
        self._tools = ToolManager()

    def generate_response(self, user_text: str, system_data: str = None) -> str:
        system_content = self.system_prompt
        if system_data:
            system_content += f"\n\nCurrent context:\n{system_data}"

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_text},
        ]

        for _ in range(_MAX_TOOL_ROUNDS):
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                tools=self._tools.get_schemas(),
                think=False,
                stream=False,
            )

            message = response["message"]
            tool_calls = message.get("tool_calls")

            if not tool_calls:
                return message["content"].strip()

            messages.append(message)

            for call in tool_calls:
                func = call["function"]
                name = func["name"]
                args = func.get("arguments", {})
                _LOG.info("Tool call: %s(%s)", name, args)
                try:
                    result = self._tools.execute(name, args)
                except Exception as exc:
                    result = f"[tool error: {exc}]"
                messages.append({
                    "role": "tool",
                    "content": result,
                    "name": name,
                })

        final = ollama.chat(
            model=self.model_name,
            messages=messages,
            tools=self._tools.get_schemas(),
            think=False,
            stream=False,
        )
        return final["message"]["content"].strip()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    llm = LocalLLM()
    print(f"Model: {llm.model_name}")
    try:
        reply = llm.generate_response("status systemet?")
        print(f"Response: {reply}")
    except Exception as e:
        print(f"Error: {e}")
