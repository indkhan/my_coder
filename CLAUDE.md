# MyAgent Project

## What this is
A personal AI agent for Usman. Qwen3 VL via Ollama is the brain.
Claude Code and Codex are tools the agent spawns — not the brain itself.
Python, Windows, Telegram interface.

## Architecture
gateway/telegram.py → brain/agent.py (Qwen ReAct loop) → tools_impl/*

## Conventions
- All async (asyncio throughout)
- Windows paths use pathlib.Path everywhere — no hardcoded slashes
- Config lives in .env, loaded via config.py — never hardcode keys
- Background tasks use asyncio.create_task(), not threading
- notify_callback(text) sends a Telegram message to Usman

## Never do
- Never hardcode TELEGRAM_TOKEN or API keys
- Never run Claude Code inside the myagent/ directory itself
- Never use blocking calls inside async functions (use asyncio.subprocess)

## Test command
python tests/test_tools.py

## Key files
- brain/agent.py: the main ReAct loop
- brain/tools.py: all tool schemas
- tools_impl/browser.py: visual browser loop (most complex)
- config.py: all env vars