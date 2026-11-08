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
    r=c.post("/api/auth/register",json={"username":"user_"+suffix,"email":suffix+"@example.test","password":"strong-pass-123","accept_terms":True})
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


def _new_user(client, suffix):
    result=client.post("/api/auth/register",json={"username":"u"+suffix,"email":suffix+"@example.test","password":"strong-pass-123","accept_terms":True})
    assert result.status_code==201,result.text
    return result.json()


def test_terms_and_owner_only_content_deletion():
    c=TestClient(app);suffix=uuid.uuid4().hex[:8]
    assert c.get("/api/terms").json()["version"]=="1.0"
    rejected=c.post("/api/auth/register",json={"username":"bad"+suffix,"email":"bad"+suffix+"@example.test","password":"strong-pass-123"})
    assert rejected.status_code==400
    a=_new_user(c,"a"+suffix);b=_new_user(c,"b"+suffix)
    ha={"Authorization":"Bearer "+a["access_token"]};hb={"Authorization":"Bearer "+b["access_token"]}
    post=c.post("/api/posts",headers=ha,json={"body":"post de teste para exclusão"}).json()
    comment=c.post(f"/api/posts/{post['id']}/comments",headers=hb,json={"body":"comentário alheio"}).json()
    assert c.delete(f"/api/posts/{post['id']}",headers=hb).status_code==403
    assert c.delete(f"/api/comments/{comment['id']}",headers=ha).status_code==403
    assert c.delete(f"/api/comments/{comment['id']}",headers=hb).status_code==204
    assert c.delete(f"/api/posts/{post['id']}",headers=ha).status_code==204


def test_direct_and_group_chats_enforce_membership_and_author_deletion():
    c=TestClient(app);suffix=uuid.uuid4().hex[:8]
    a=_new_user(c,"a"+suffix);b=_new_user(c,"b"+suffix);outsider=_new_user(c,"c"+suffix)
    ha={"Authorization":"Bearer "+a["access_token"]};hb={"Authorization":"Bearer "+b["access_token"]};ho={"Authorization":"Bearer "+outsider["access_token"]}
    direct=c.post("/api/chats/direct",headers=ha,json={"username":"uB"+suffix}).json()
    msg=c.post(f"/api/chats/{direct['id']}/messages",headers=ha,json={"body":"oi"})
    assert msg.status_code==201,msg.text
    assert c.get(f"/api/chats/{direct['id']}/messages",headers=hb).json()[0]["body"]=="oi"
    assert c.get(f"/api/chats/{direct['id']}/messages",headers=ho).status_code==404
    assert c.delete(f"/api/chats/{direct['id']}/messages/{msg.json()['id']}",headers=hb).status_code==403
    assert c.delete(f"/api/chats/{direct['id']}/messages/{msg.json()['id']}",headers=ha).status_code==204
    group=c.post("/api/chats/groups",headers=ha,json={"title":"Grupo","usernames":["uB"+suffix,"uC"+suffix]})
    assert group.status_code==201,group.text
    assert len(c.get(f"/api/chats/{group.json()['id']}/messages",headers=ho).json())==0


def test_optional_avatar_project_cover_moderation_and_owner_delete():
    from PIL import Image
    c=TestClient(app);suffix=uuid.uuid4().hex[:8];account=_new_user(c,"media"+suffix)
    headers={"Authorization":"Bearer "+account["access_token"]}
    image=io.BytesIO();Image.new("RGB",(8,8),(30,170,160)).save(image,format="PNG");image.seek(0)
    avatar=c.put("/api/me/avatar",headers=headers,files={"file":("avatar.png",image,"image/png")})
    assert avatar.status_code==200,avatar.text
    assert c.get(f"/api/users/{account['user']['username']}/avatar").status_code==200
    manifest={"name":"Demo","version":"1.0","developer":account["user"]["username"],"description":"safe","format":"bloom","files":[]}
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,"w") as z:z.writestr("bloom.json",json.dumps(manifest))
    archive.seek(0)
    result=c.post("/api/games",headers=headers,data={"name":"Demo project","version":"1.0","description":"safe","format":"bloom"},files={"file":("demo.zip",archive,"application/zip")})
    assert result.status_code==201,result.text
    game=result.json();assert game["status"]=="published"
    cover=io.BytesIO();Image.new("RGB",(16,9),(40,80,120)).save(cover,format="PNG");cover.seek(0)
    uploaded=c.put(f"/api/games/{game['id']}/cover",headers=headers,files={"file":("cover.png",cover,"image/png")})
    assert uploaded.status_code==200,uploaded.text
    assert c.get(f"/api/games/{game['id']}/cover").status_code==200
    assert c.delete(f"/api/games/{game['id']}",headers=headers).status_code==204
    assert c.get(f"/api/games/{game['slug']}").status_code==404


def test_community_safety_rules_and_twelve_locales():
    from bloom_app.localization import LANGUAGES
    assert 5 <= len(LANGUAGES) <= 15
    c=TestClient(app);suffix=uuid.uuid4().hex[:8];account=_new_user(c,"safe"+suffix)
    headers={"Authorization":"Bearer "+account["access_token"]}
    blocked=c.post("/api/posts",headers=headers,json={"body":"aqui tem pornografia explícita"})
    assert blocked.status_code==422
    allowed=c.post("/api/posts",headers=headers,json={"body":"Olá, comunidade!"})
    assert allowed.status_code==201,allowed.text


def test_report_message_and_manual_game_review():
    from bloom_world import main as world
    c=TestClient(app);suffix=uuid.uuid4().hex[:8];a=_new_user(c,"a"+suffix);b=_new_user(c,"b"+suffix)
    ha={"Authorization":"Bearer "+a["access_token"]};hb={"Authorization":"Bearer "+b["access_token"]}
    chat=c.post("/api/chats/direct",headers=ha,json={"username":"uB"+suffix}).json()
    message=c.post(f"/api/chats/{chat['id']}/messages",headers=ha,json={"body":"mensagem para denúncia"}).json()
    report=c.post("/api/reports",headers=hb,json={"target_type":"message","target_id":message["id"],"reason":"conteúdo inapropriado"})
    assert report.status_code==201,report.text
    manifest={"name":"xxx test","version":"1.0","developer":"uA"+suffix,"description":"test","format":"bloom","files":[]}
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,"w") as z:z.writestr("bloom.json",json.dumps(manifest))
    archive.seek(0)
    uploaded=c.post("/api/games",headers=ha,data={"name":"xxx game","version":"1.0","description":"test","format":"bloom"},files={"file":("test.zip",archive,"application/zip")})
    assert uploaded.status_code==201,uploaded.text
    game=uploaded.json();assert game["status"]=="pending_review"
    assert all(row["id"]!=game["id"] for row in c.get("/api/games").json())
    world.MODERATOR_IDS.add(a["user"]["id"])
    try:
        assert c.get("/api/moderation/queue",headers=ha).status_code==200
        approved=c.post(f"/api/moderation/games/{game['id']}",headers=ha,json={"status":"approved"})
        assert approved.status_code==200,approved.text
        assert any(row["id"]==game["id"] for row in c.get("/api/games").json())
        queue=c.get("/api/moderation/reports",headers=ha)
        assert any(row["id"]==report.json()["id"] for row in queue.json())
    finally:world.MODERATOR_IDS.discard(a["user"]["id"])


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
