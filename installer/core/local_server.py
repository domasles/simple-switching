import socketserver
import http.server
import threading

from typing import Optional
from pathlib import Path


class LocalServer:
    """Hosts a multi-threaded HTTP server on localhost serving update and extension information."""

    def __init__(self, serve_dir: Path, port: int = 0):
        self.serve_dir = serve_dir.resolve()
        self.port = port
        self.httpd: Optional[socketserver.ThreadingTCPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        serve_directory = str(self.serve_dir)
        self.serve_dir.mkdir(parents=True, exist_ok=True)

        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            extensions_map = {
                **http.server.SimpleHTTPRequestHandler.extensions_map,
                ".crx": "application/x-chrome-extension",
                ".xml": "text/xml; charset=utf-8",
            }

            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=serve_directory, **kwargs)

            def log_message(self, format, *args):
                pass

        # Ensure port can be rebound cleanly
        socketserver.ThreadingTCPServer.allow_reuse_address = True

        # Use ThreadingTCPServer to support concurrent download requests
        self.httpd = socketserver.ThreadingTCPServer(("127.0.0.1", self.port), CustomHandler)
        self.port = self.httpd.server_address[1]

        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def get_url(self, file_path: str) -> str:
        return f"http://127.0.0.1:{self.port}/{file_path.lstrip('/')}"

    def stop(self) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
