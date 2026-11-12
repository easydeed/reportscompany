"""A stand-in for SendGrid's HTTP API, in its own process, for the LR-023 live run.

Every POST is appended to posts.log as "<recipient>\t<behaviour>". The
behaviour for the next POST comes from control.json:
  {"mode": "202"}            accept everything
  {"mode": "drop_first"}     read the first POST in full, close with no answer
                             (accepted, answer lost); 202 for the rest
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).parent
PORT = int(sys.argv[1])


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        email = body["personalizations"][0]["to"][0]["email"]
        ctl = json.loads((HERE / "control.json").read_text())
        how = "202"
        if ctl.get("mode") == "drop_first" and not ctl.get("dropped"):
            how = "drop"
            ctl["dropped"] = True
            (HERE / "control.json").write_text(json.dumps(ctl))
        with open(HERE / "posts.log", "a") as f:
            f.write(f"{email}\t{how}\n")
        if how == "drop":
            self.close_connection = True
            return
        self.send_response(202)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"{}")


ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
