"""桌面壳入口：使用 PyWebView 创建原生窗口"""
import sys
import socket
import threading
import time
from pathlib import Path

# 将项目根目录加入 sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import webview
import uvicorn

from backend.main import app


def find_free_port(start=18700, end=18800):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No free port available")


def start_server(port):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def wait_for_server(port, retries=10, interval=0.5):
    for _ in range(retries):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(interval)
    raise RuntimeError(f"Server on port {port} failed to start")


def main():
    port = find_free_port()

    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()
    wait_for_server(port)

    window = webview.create_window(
        title="MiMo TTS Studio",
        url=f"http://127.0.0.1:{port}",
        width=1200,
        height=800,
        min_size=(900, 600),
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
