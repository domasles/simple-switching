import socketserver
import http.server
import threading

from pathlib import Path
from typing import Optional


class LocalServer:
    """Hosts an HTTP server on localhost serving update and extension information."""

    def __init__(self, serve_dir: Path, port: int = 0):
        self.serve_dir = serve_dir.resolve()
        self.port = port
        self.httpd: Optional[socketserver.TCPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        serve_directory = str(self.serve_dir)

        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(*args, **kwargs):
                super().__init__(*args, directory=serve_directory, **kwargs)

            def log_message(self, format, *args):
                pass

        self.httpd = socketserver.TCPServer(("127.0.0.1", self.port), QuietHandler)
        self.port = self.httpd.server_address[1]

        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def get_url(self, file_path: str) -> str:
        return f"http://127.0.0.1:{self.port}/{file_path.lstrip('/')}"

    def stop(self) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
