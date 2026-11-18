"""Janela desktop BLOOM para a experiência web empacotada."""
from __future__ import annotations

import os
import sys
import subprocess
import threading
import urllib.parse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def bundled_web_dir() -> Path:
    """Encontra web/ tanto durante desenvolvimento quanto no bundle PyInstaller."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / "web"


class BloomBridge:
    """Native bridge for the existing Windows client and local tools."""
    def open_local_tools(self) -> bool:
        if getattr(sys, "frozen", False):
            command = [sys.executable, "--classic"]
        else:
            command = [sys.executable, "-m", "bloom_app.main"]
        subprocess.Popen(command, cwd=str(Path(__file__).resolve().parent.parent), close_fds=True)
        return True


def main() -> None:
    if "--classic" in sys.argv:
        from bloom_app.main import BloomApp
        BloomApp().mainloop()
        return
    try:
        import webview
    except ImportError as exc:
        raise SystemExit("Instale pywebview com: pip install pywebview") from exc

    root = bundled_web_dir()
    if not (root / "index.html").is_file():
        raise SystemExit(f"Arquivos web não encontrados: {root}")

    try:
        from bloom_app.build_config import API_URL
    except ImportError:
        API_URL = "https://bloom-world.onrender.com"
    api_url = os.environ.get("BLOOM_API_URL", API_URL).strip().rstrip("/")
    if not api_url.startswith(("https://", "http://127.0.0.1", "http://localhost")):
        raise SystemExit("BLOOM_API_URL deve usar HTTPS para servidores públicos.")

    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, name="bloom-assets", daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_address[1]}/?api={urllib.parse.quote(api_url, safe=':/')}"
    try:
        webview.create_window(
            "BLOOM — Created by ZYXZXM.",
            url,
            width=1440,
            height=920,
            min_size=(960, 650),
            background_color="#c4f2f6",
            js_api=BloomBridge(),
        )
        webview.start(gui="edgechromium", debug=False)
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
