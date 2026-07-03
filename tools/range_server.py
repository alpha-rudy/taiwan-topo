import http.server, socketserver, sys, os, re

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8030
ROOT = sys.argv[2] if len(sys.argv) > 2 else "."
os.chdir(ROOT)

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        rng = self.headers.get("Range", "-")
        code = args[1] if len(args) >= 2 else "-"
        rl = getattr(self, "requestline", "?")
        sys.stdout.write("REQ %s -> %s  Range=%s\n" % (rl, code, rng))
        sys.stdout.flush()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_GET(self):
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().do_GET()
        m = re.match(r"bytes=(\d+)-(\d*)", rng)
        if not m:
            return super().do_GET()
        size = os.path.getsize(path)
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else size - 1
        end = min(end, size - 1)
        length = end - start + 1
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

socketserver.ThreadingTCPServer.allow_reuse_address = True
with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), H) as httpd:
    sys.stdout.write("SERVING %s on port %d\n" % (os.getcwd(), PORT))
    sys.stdout.flush()
    httpd.serve_forever()
