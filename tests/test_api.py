from pathlib import Path

from fastapi.testclient import TestClient

from scripts.serve import app

SAMPLES = Path(__file__).resolve().parent.parent / "data" / "samples"
client = TestClient(app)


def test_healthz():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_detect_contract_is_exact():
    with open(SAMPLES / "sample_2.png", "rb") as f:
        r = client.post("/detect", files={"file": ("sample_2.png", f, "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert list(body.keys()) == ["boxes"]
    assert len(body["boxes"]) > 50
    for b in body["boxes"]:
        assert list(b.keys()) == ["bbox", "is_checked"]
        x1, y1, x2, y2 = b["bbox"]
        assert all(isinstance(v, int) for v in b["bbox"])
        assert x2 > x1 and y2 > y1
        assert isinstance(b["is_checked"], bool)


def test_detect_explain_adds_evidence():
    with open(SAMPLES / "sample_1.jpg", "rb") as f:
        r = client.post("/detect?explain=true", files={"file": ("sample_1.jpg", f, "image/jpeg")})
    body = r.json()
    assert "meta" in body and body["meta"]["width"] == 1586
    assert {"confidence", "ink", "reasons", "witnesses"} <= set(body["boxes"][0].keys())


def test_non_image_is_rejected():
    r = client.post("/detect", files={"file": ("x.txt", b"not an image", "text/plain")})
    assert r.status_code == 400


def test_overlay_is_png():
    with open(SAMPLES / "sample_7.png", "rb") as f:
        r = client.post("/detect/overlay", files={"file": ("sample_7.png", f, "image/png")})
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"
