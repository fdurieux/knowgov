"""One reader call for another subject (task-0157, B7; decision-0013, design (a)): the reader started on
one subject answers a call that names another by running this, a child process with that subject's
``KG_SUBJECT``, the session's date and the code leg's instance and ledger in its environment, so the child
answers exactly as a reader started on that subject would. It reads the call (``{"name", "arguments"}``)
on stdin and writes the JSON-RPC result on stdout, then exits; it never routes again and never writes the
store. Standard library only.

    KG_SUBJECT=<root> python harness/mcp_child.py < call.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> int:
    import mcp_server
    call = json.loads(sys.stdin.read() or "{}")
    server = mcp_server.Server(mcp_server.Tools(), route=None)   # the child answers its own subject only
    import upward
    server.tools.trace_cfg = upward.config()   # KG_INSTANCE and KG_LEDGER, as the parent read them at start
    resp = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                          "params": {"name": call.get("name"), "arguments": call.get("arguments") or {}}})
    sys.stdout.write(json.dumps(resp.get("result") if "result" in resp else {"error": resp.get("error")},
                                ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    import cli_exit   # task-0314 R5
    cli_exit.help_exit(__doc__)
    sys.exit(main())
