from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.protocol.http.app import create_app


def test_error_envelope_for_http_exception() -> None:
    app: FastAPI = create_app()

    @app.get("/boom")
    def boom():  # type: ignore[no-redef]
        raise HTTPException(status_code=400, detail="oops")

    client = TestClient(app)
    r = client.get("/boom")
    assert r.status_code == 400
    body = r.json()
    assert "error" in body
    err = body["error"]
    assert err["code"] == "bad_request"
    assert err["message"] == "oops"
    assert err["type"] == "client_error"
    assert err["request_id"]
