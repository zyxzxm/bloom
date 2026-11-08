import io, json, zipfile, uuid
from pathlib import Path
from fastapi.testclient import TestClient
from bloom_world.main import app
from bloom_safe.scanner import inspect_package
from bloom_safe.installer import safe_extract


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
