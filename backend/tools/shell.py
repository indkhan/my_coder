"""Shell command tool."""

from __future__ import annotations

import asyncio
from typing import Any

from backend.agent.models import RiskLevel
from backend.tools.base import BaseTool, ToolResult

DEFAULT_TIMEOUT = 120  # seconds


class RunCommandTool(BaseTool):
    name = "run_command"
    description = "Execute a shell command and return stdout/stderr"
    risk_level = RiskLevel.HIGH
    parameters_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 120)",
            },
        },
        "required": ["command"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        command = kwargs["command"]
        timeout = kwargs.get("timeout", DEFAULT_TIMEOUT)
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            output = stdout.decode(errors="replace")
            err = stderr.decode(errors="replace")
            if proc.returncode != 0:
                return ToolResult(
                    success=False,
                    output=output,
                    error=f"Exit code {proc.returncode}\n{err}",
                )
            return ToolResult(success=True, output=output + err)
        except asyncio.TimeoutError:
            proc.kill()
            return ToolResult(success=False, error=f"Command timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
