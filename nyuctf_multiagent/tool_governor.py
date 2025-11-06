"""tool governor for mapping categories to recommended tools.

this module exposes a simple mapping and chooser; production code should rely on the environment's toolset instead of raw shell commands.
"""
from typing import List

TOOL_MAP = {
    "pwn": ["checksec", "ropper"],
    "web": ["curl -I", "sqlmap --batch"],
    "crypto": ["python3 solve.py"],
    "rev": ["ghidra_headless", "r2 -A"],
}


def choose_tools(category: str, hint: str = "") -> List[str]:
    """return a list of suggested tools for a category.

    this is heuristic; treat as hints and consult the environment for actual runnable tool names.
    """
    return TOOL_MAP.get(category, ["strings", "file"])
