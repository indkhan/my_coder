"""Filesystem tools."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from backend.agent.models import RiskLevel
from backend.tools.base import BaseTool, ToolResult

MAX_READ_SIZE = 1_000_000  # 1 MB


class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List files and directories at a given path"
    risk_level = RiskLevel.LOW
    parameters_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to list",
            }
        },
        "required": ["path"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = Path(kwargs["path"])
        if not path.is_dir():
            return ToolResult(success=False, error=f"Not a directory: {path}")
        try:
            entries = sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())
            return ToolResult(success=True, output="\n".join(entries))
        except PermissionError as e:
            return ToolResult(success=False, error=str(e))


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read and return the contents of a file"
    risk_level = RiskLevel.LOW
    parameters_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read",
            }
        },
        "required": ["file_path"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = Path(kwargs["file_path"])
        if not path.is_file():
            return ToolResult(success=False, error=f"File not found: {path}")
        if path.stat().st_size > MAX_READ_SIZE:
            return ToolResult(success=False, error=f"File too large (>{MAX_READ_SIZE} bytes)")
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            return ToolResult(success=True, output=content)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write content to a file, creating parent directories if needed"
    risk_level = RiskLevel.MEDIUM
    parameters_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to write to",
            },
            "content": {
                "type": "string",
                "description": "Content to write",
            },
        },
        "required": ["file_path", "content"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = Path(kwargs["file_path"])
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(kwargs["content"], encoding="utf-8")
            return ToolResult(success=True, output=f"Written to {path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class EditFileDiffTool(BaseTool):
    name = "edit_file"
    description = "Edit a file by replacing a search string with a replacement string"
    risk_level = RiskLevel.MEDIUM
    parameters_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to edit",
            },
            "old_string": {
                "type": "string",
                "description": "The exact string to find and replace",
            },
            "new_string": {
                "type": "string",
                "description": "The replacement string",
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = Path(kwargs["file_path"])
        if not path.is_file():
            return ToolResult(success=False, error=f"File not found: {path}")
        try:
            content = path.read_text(encoding="utf-8")
            old = kwargs["old_string"]
            if old not in content:
                return ToolResult(success=False, error="Search string not found in file")
            count = content.count(old)
            if count > 1:
                return ToolResult(success=False, error=f"Search string found {count} times; must be unique")
            new_content = content.replace(old, kwargs["new_string"], 1)
            path.write_text(new_content, encoding="utf-8")
            return ToolResult(success=True, output=f"Edited {path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CreateDirectoryTool(BaseTool):
    name = "create_directory"
    description = "Create a directory (and parent directories)"
    risk_level = RiskLevel.MEDIUM
    parameters_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to create",
            }
        },
        "required": ["path"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        try:
            os.makedirs(kwargs["path"], exist_ok=True)
            return ToolResult(success=True, output=f"Created {kwargs['path']}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Delete a file or directory"
    risk_level = RiskLevel.HIGH
    parameters_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to delete",
            }
        },
        "required": ["path"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = Path(kwargs["path"])
        if not path.exists():
            return ToolResult(success=False, error=f"Path not found: {path}")
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            return ToolResult(success=True, output=f"Deleted {path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
