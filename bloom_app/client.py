"""Cliente HTTP do BLOOM, separado da interface Tkinter para facilitar testes."""
import json
from pathlib import Path
import httpx


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


class BloomClient:
    def __init__(self, config_path: Path, state_path: Path, default_config=None):
        self.config_path = Path(config_path)
        self.state_path = Path(state_path)
        defaults = dict(default_config or {})
        saved = read_json(self.config_path, {})
        if not isinstance(saved, dict):
            saved = {}
        self.config = {**defaults, **saved}
        default_api = defaults.get("api_url")
        if default_api and not saved.get("api_url_default_migrated"):
            old_api = str(saved.get("api_url", "")).strip().rstrip("/")
            if old_api in {"", "http://127.0.0.1:8000", "http://localhost:8000"}:
                self.config["api_url"] = default_api
            self.config["api_url_default_migrated"] = True
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(json.dumps(self.config, ensure_ascii=False), encoding="utf-8")
        self.state = read_json(self.state_path, {})

    @property
    def base(self):
        return self.config.get("api_url", "").rstrip("/")

    def request(self, method, path, **kwargs):
        if not self.base:
            raise RuntimeError("O BLOOM ainda não está conectado ao serviço online. Baixe a versão oficial configurada pelo publicador.")
        headers = dict(kwargs.pop("headers", {}) or {})
        token = self.state.get("access_token") or self.state.get("token")
        if token:
            headers["Authorization"] = "Bearer " + token
        with httpx.Client(timeout=40) as client:
            return client.request(method, self.base + path, headers=headers, **kwargs)

    def auth(self, method, payload):
        response = self.request("POST", f"/api/auth/{method}", json=payload)
        response.raise_for_status()
        self.state = response.json()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state), encoding="utf-8")
