# MyAgent - Codex Instructions

## Project
Personal AI agent. Python, Windows, asyncio. Qwen3 VL is the brain.

## Rules
- Use pathlib.Path for all file paths (Windows compatibility)
- All I/O must be async — use asyncio.subprocess not subprocess directly
- No blocking calls in async functions
- Error handling: all tool functions return strings, never raise to caller
- Timeouts: shell=30s, claude_code=300s, browser_step=10s

## Test after every implementation
python tests/test_tools.py

## Autonomy
Work autonomously. Do not ask for confirmation mid-task.
Do not narrate your plan before starting. Just implement and verify.