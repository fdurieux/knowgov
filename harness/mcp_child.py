"""SPIKE (task-0151): design (a)'s child. One tools/call on the reader for the subject KG_SUBJECT
names, printed as the JSON-RPC result, then exit. Never merged."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mcp_server  # noqa: E402


def main(argv: list[str]) -> int:
    tool, args = argv[0], json.loads(argv[1]) if len(argv) > 1 else {}
    server = mcp_server.Server(mcp_server.Tools())
    resp = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": args}})
    sys.stdout.write(json.dumps(resp["result"], ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
