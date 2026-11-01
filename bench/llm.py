"""One model call through the `claude` CLI (subscription auth), stripped of local settings, tools,
MCP servers and skills so the only context is the prompt. Returns the CLI's JSON result."""
import json
import os
import subprocess
import tempfile
import time

CLAUDE = os.environ.get("CLAUDE_BIN", os.path.expanduser("~/.local/bin/claude"))
EMPTY = tempfile.mkdtemp(prefix="bench-cwd-")       # no CLAUDE.md is picked up from here


def ask(prompt, system="You answer questions.", model="sonnet", retries=4):
    cmd = [CLAUDE, "-p", "--model", model, "--output-format", "json", "--tools", "",
           "--no-session-persistence", "--system-prompt", system, "--strict-mcp-config",
           "--setting-sources", "", "--disable-slash-commands"]
    for attempt in range(retries):
        t0 = time.time()
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=EMPTY, timeout=600)
        try:
            out = json.loads(r.stdout)
            if not out.get("is_error"):
                out["wall_s"] = time.time() - t0
                return out
        except json.JSONDecodeError:
            pass
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"claude call failed: {r.stderr[-500:]} {r.stdout[-500:]}")
