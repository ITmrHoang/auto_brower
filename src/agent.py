"""
Agent module for Auto-Browser.
Provides natural language command parsing for browser automation.
Can work with or without an AI API key.
"""

import re
from typing import Optional, List, Tuple

from rich.console import Console

console = Console()


# Rule-based command parser (no API key required)
COMMAND_PATTERNS = [
    # Navigation
    (r"(?:mở|open|go to|navigate to|vào)\s+(.+)", "goto {0}"),
    (r"(?:tìm kiếm|search|tìm)\s+(.+?)(?:\s+(?:trên|on)\s+(.+))?$", "_search"),
    (r"(?:quay lại|go back|back)", "back"),
    (r"(?:tiếp|forward|go forward)", "forward"),
    (r"(?:tải lại|reload|refresh|làm mới)", "reload"),

    # Interaction
    (r"(?:nhấn|click|bấm)\s+(?:vào\s+)?(.+)", "click {0}"),
    (r"(?:gõ|nhập|type|enter)\s+['\"](.+?)['\"]\s+(?:vào|into|in)\s+(.+)", "type {1} {0}"),
    (r"(?:gõ|nhập|type|enter)\s+(.+?)(?:\s+(?:vào|into|in)\s+(.+))?$", "_type"),
    (r"(?:chụp ảnh|screenshot|chụp màn hình)", "screenshot"),

    # Browser management
    (r"(?:đóng|close)\s+(?:trình duyệt|browser)?\s*(.+)?", "_close"),
    (r"(?:danh sách|list|liệt kê|xem)", "list"),
    (r"(?:đợi|wait|chờ)\s+(\d+)\s*(?:giây|s|seconds?)?", "_wait"),

    # Script
    (r"(?:chạy|run|execute)\s+(?:script|file)\s+(.+)", "script {0}"),
    (r"(?:chạy|run|execute)\s+(.+\.js)", "script {0}"),
]


def parse_natural_language(text: str) -> Optional[str]:
    """
    Parse natural language (Vietnamese or English) into a chat command.
    Returns None if no match found.
    """
    text = text.strip()

    for pattern, template in COMMAND_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()

            if template == "_search":
                query = groups[0]
                site = groups[1] if len(groups) > 1 and groups[1] else "google.com"
                if "google" in site.lower():
                    return f'goto https://www.google.com/search?q={query.replace(" ", "+")}'
                elif "youtube" in site.lower():
                    return f'goto https://www.youtube.com/results?search_query={query.replace(" ", "+")}'
                else:
                    return f'goto https://www.google.com/search?q={query.replace(" ", "+")}+site:{site}'

            elif template == "_type":
                text_val = groups[0]
                selector = groups[1] if len(groups) > 1 and groups[1] else "input"
                return f"type {selector} {text_val}"

            elif template == "_close":
                profile = groups[0].strip() if groups[0] else ""
                return f"close {profile}" if profile else "close"

            elif template == "_wait":
                seconds = int(groups[0])
                return f"wait {seconds * 1000}"

            else:
                cmd = template
                for i, g in enumerate(groups):
                    if g:
                        cmd = cmd.replace(f"{{{i}}}", g.strip())
                return cmd

    return None


class Agent:
    """
    Agent that translates natural language commands to browser actions.
    Uses rule-based parsing by default, can be extended with AI API.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.use_ai = api_key is not None

    async def process(self, text: str) -> Optional[str]:
        """
        Process a natural language command and return a chat command string.
        """
        # First try rule-based parsing
        result = parse_natural_language(text)
        if result:
            console.print(f"[dim]→ Parsed: {result}[/dim]")
            return result

        # If AI is available, try AI parsing
        if self.use_ai:
            return await self._ai_parse(text)

        console.print(f"[yellow]Không hiểu lệnh. Gõ 'help' để xem danh sách lệnh.[/yellow]")
        return None

    async def _ai_parse(self, text: str) -> Optional[str]:
        """
        Use AI to parse natural language. Placeholder for AI integration.
        Can be extended with OpenAI/Google AI SDK.
        """
        # TODO: Integrate with AI API when available
        # Example with OpenAI:
        # response = await openai.chat.completions.create(
        #     model="gpt-4",
        #     messages=[
        #         {"role": "system", "content": SYSTEM_PROMPT},
        #         {"role": "user", "content": text}
        #     ]
        # )
        # return response.choices[0].message.content
        console.print(f"[yellow]AI agent not configured. Using rule-based parsing only.[/yellow]")
        return None
