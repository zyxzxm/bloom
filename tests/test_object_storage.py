import httpx

from bloom_world import object_storage


def test_supabase_storage_upload_download_delete(monkeypatch, tmp_path):
    saved = {"path": None, "payload": None}

    def handler(request):
        if request.method == "POST":
            saved["path"] = request.url.path
            saved["payload"] = request.read()
            assert request.headers["x-upsert"] == "true"
            return httpx.Response(200, json={"Key": "bloom-assets/packages/test.zip"})
        if request.method == "GET":
            assert request.url.path.endswith("/bloom-assets/packages/test.zip")
            return httpx.Response(200, content=saved["payload"])
        if request.method == "DELETE":
            assert request.read() == b'{"prefixes":["packages/test.zip"]}'
            return httpx.Response(200, json={"message": "Successfully deleted"})
        return httpx.Response(405)

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(object_storage.httpx, "Client", lambda *a, **kw: real_client(*a, transport=transport, **kw))
    monkeypatch.setattr(object_storage, "SUPABASE_URL", "https://bloom.example.supabase.co")
    monkeypatch.setattr(object_storage, "SUPABASE_SERVICE_ROLE_KEY", "test-secret")
    monkeypatch.setattr(object_storage, "BUCKET", "bloom-assets")

    source = tmp_path / "test.zip"
    source.write_bytes(b"fake zip bytes")
    object_storage.upload_file(source, "packages/test.zip", "application/zip")
    destination = tmp_path / "downloaded.zip"
    object_storage.download_file("packages/test.zip", destination)
    assert destination.read_bytes() == b"fake zip bytes"
    object_storage.delete_object("packages/test.zip")
    assert saved["path"].endswith("/bloom-assets/packages/test.zip")
