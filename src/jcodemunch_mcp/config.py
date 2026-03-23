"""Centralized JSONC config for jcodemunch-mcp."""

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _strip_jsonc(text: str) -> str:
    """Strip // and /* */ comments from JSONC, respecting quoted strings."""
    result, i, n = [], 0, len(text)
    in_str = False
    while i < n:
        ch = text[i]
        if in_str:
            result.append(ch)
            if ch == '\\' and i + 1 < n:
                result.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_str = False
            i += 1
        elif ch == '"':
            in_str = True
            result.append(ch)
            i += 1
        elif ch == '/' and i + 1 < n and text[i + 1] == '/':
            # Line comment — skip to end of line
            end = text.find('\n', i)
            i = n if end == -1 else end
        elif ch == '/' and i + 1 < n and text[i + 1] == '*':
            # Block comment — skip to */
            end = text.find('*/', i + 2)
            i = n if end == -1 else end + 2
        else:
            result.append(ch)
            i += 1
    return ''.join(result)
