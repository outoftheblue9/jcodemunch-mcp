"""Tests for JSONC config parsing."""

import pytest

from src.jcodemunch_mcp.config import _strip_jsonc


class TestJSONCParser:
    """Test JSONC comment stripping."""

    def test_strips_line_comments(self):
        """Should strip // comments to end of line."""
        text = '{"key": "value" // this is a comment\n}'
        result = _strip_jsonc(text)
        assert result == '{"key": "value" \n}'

    def test_strips_line_comment_no_trailing_newline(self):
        """Should strip // comment at end of file."""
        text = '{"key": "value"} // comment'
        result = _strip_jsonc(text)
        assert result == '{"key": "value"} '
