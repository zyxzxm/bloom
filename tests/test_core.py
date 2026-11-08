import io, json, os, shutil, tempfile, zipfile, uuid
from pathlib import Path

# Os testes nunca devem escrever no banco ou armazenamento usados pela API local.
_TEST_ROOT = Path(tempfile.gettempdir()) / f"bloom-tests-{uuid.uuid4().hex}"
_TEST_ROOT.mkdir(parents=True, exist_ok=True)
_TEST_DB = _TEST_ROOT / "test.sqlite3"
os.environ["BLOOM_DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"
os.environ["BLOOM_DATA_DIR"] = str(_TEST_ROOT / "data")

import pytest
from fastapi.testclient import TestClient
from bloom_world.main import app
from bloom_world.database import engine
from bloom_safe.scanner import inspect_package
from bloom_safe.installer import safe_extract


@pytest.fixture(scope="session", autouse=True)
def cleanup_isolated_test_data():
    yield
    engine.dispose()
    shutil.rmtree(_TEST_ROOT, ignore_errors=True)


def test_scanner_hash_and_risk(tmp_path):
    package=tmp_path/"sample.zip"
    with zipfile.ZipFile(package,"w") as z:
        z.writestr("bloom.json",json.dumps({"name":"x","version":"1","developer":"dev","description":"x","format":"bloom","files":[]}))
        z.writestr("start.bat","echo hi")
    report=inspect_package(package)
    assert len(report["sha256"])==64
    assert report["findings"]
    assert "Nenhuma verificação garante segurança" in report["disclaimer"]


def test_safe_extract_rejects_windows_zip_slip(tmp_path):
    package=tmp_path/"evil.zip"
    with zipfile.ZipFile(package,"w") as z:z.writestr("..\\outside.txt","malicious")
    try:
        safe_extract(package,tmp_path/"install")
        assert False, "O extrator deveria rejeitar o caminho"
    except ValueError as exc:
        assert "caminho inseguro" in str(exc)


def test_api_auth_social_and_catalog():
    c=TestClient(app);suffix=uuid.uuid4().hex[:12]
    r=c.post("/api/auth/register",json={"username":"user_"+suffix,"email":suffix+"@example.test","password":"strong-pass-123"})
    assert r.status_code==201,r.text
    token=r.json()["access_token"];h={"Authorization":"Bearer "+token}
    r=c.post("/api/posts",headers=h,json={"body":"Olá comunidade BLOOM"});assert r.status_code==201,r.text
    post_id=r.json()["id"]
    assert c.get("/api/posts").status_code==200
    assert c.post(f"/api/posts/{post_id}/like",headers=h).json()["liked"] is True
    comment=c.post(f"/api/posts/{post_id}/comments",headers=h,json={"body":"Belo projeto!"})
    assert comment.status_code==201,comment.text
    assert c.get("/api/posts/{}/comments".format(post_id)).json()[0]["body"]=="Belo projeto!"
    assert c.get("/api/games").status_code==200
    assert c.get("/health").json()["status"]=="ok"


def test_desktop_client_sends_api_access_token(monkeypatch, tmp_path):
    from bloom_app.client import BloomClient

    captured = {}

    class FakeClient:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def request(self, method, url, **kwargs):
            captured.update(kwargs.get("headers", {}))
            return object()

    monkeypatch.setattr("bloom_app.client.httpx.Client", FakeClient)
    client = BloomClient(tmp_path / "settings.json", tmp_path / "state.json")
    client.config = {"api_url": "http://127.0.0.1:8000"}
    client.state = {"access_token": "test-token", "token_type": "bearer"}
    client.request("POST", "/api/posts", json={"body": "teste"})
    assert captured["Authorization"] == "Bearer test-token"
