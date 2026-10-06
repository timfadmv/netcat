"""
Tests for the HTTP security headers reported by the ZAP baseline scan (issue #17)
and for the frontend rules required by a strict Content-Security-Policy.
"""
import re
from pathlib import Path

import pytest

from app import app

ROOT = Path(__file__).resolve().parent.parent

PAGES = ["/", "/static/script.js", "/static/style.css"]


@pytest.fixture()
def client():
    return app.test_client()


@pytest.mark.parametrize("path", PAGES)
def test_nosniff(client, path):
    assert client.get(path).headers.get("X-Content-Type-Options") == "nosniff"


@pytest.mark.parametrize("path", PAGES)
def test_clickjacking_protection(client, path):
    response = client.get(path)
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "frame-ancestors 'none'" in response.headers.get("Content-Security-Policy", "")


@pytest.mark.parametrize("path", PAGES)
def test_csp_is_strict(client, path):
    csp = client.get(path).headers.get("Content-Security-Policy", "")
    directives = {d.split()[0]: d.split()[1:] for d in csp.split(";") if d.strip()}

    assert directives.get("default-src") == ["'self'"]
    assert directives.get("script-src") == ["'self'"]
    assert directives.get("object-src") == ["'none'"]
    assert directives.get("base-uri") == ["'none'"]
    assert "'unsafe-inline'" not in csp
    assert "'unsafe-eval'" not in csp


@pytest.mark.parametrize("path", PAGES)
def test_cross_origin_isolation_headers(client, path):
    response = client.get(path)
    assert response.headers.get("Cross-Origin-Opener-Policy") == "same-origin"
    assert response.headers.get("Cross-Origin-Resource-Policy") == "same-origin"
    assert response.headers.get("Cross-Origin-Embedder-Policy") == "require-corp"


@pytest.mark.parametrize("path", PAGES)
def test_permissions_and_referrer_policy(client, path):
    response = client.get(path)
    assert "camera=()" in response.headers.get("Permissions-Policy", "")
    assert response.headers.get("Referrer-Policy") == "no-referrer"


def test_api_responses_are_not_cached(client):
    response = client.post("/api/close", json={"connection_id": "does-not-exist"})
    assert response.headers.get("Cache-Control") == "no-store"


def test_headers_are_also_set_on_error_responses(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")


# --- A strict CSP blocks inline handlers and inline styles, so the frontend must not use them.

FRONTEND_FILES = [ROOT / "templates" / "index.html", ROOT / "static" / "script.js"]


@pytest.mark.parametrize("path", FRONTEND_FILES, ids=lambda p: p.name)
def test_no_inline_event_handlers(path):
    # e.g. onclick="...", onkeypress="..."
    assert not re.search(r"\son[a-z]+\s*=", path.read_text()), f"inline handler in {path.name}"


@pytest.mark.parametrize("path", FRONTEND_FILES, ids=lambda p: p.name)
def test_no_inline_style_attributes(path):
    assert not re.search(r"\sstyle\s*=", path.read_text()), f"inline style in {path.name}"


def test_no_inline_script_blocks():
    html = (ROOT / "templates" / "index.html").read_text()
    assert not re.search(r"<script(?![^>]*\ssrc=)[^>]*>", html), "inline <script> block"
