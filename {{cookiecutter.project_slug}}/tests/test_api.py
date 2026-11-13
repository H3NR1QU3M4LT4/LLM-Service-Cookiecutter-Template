from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from {{ cookiecutter.package_name }}.api import app

client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_returns_answer() -> None:
    with patch("{{ cookiecutter.package_name }}.api.answer", new=AsyncMock(return_value="42")):
        response = client.post("/ask", json={"question": "Meaning of life?"})

    assert response.status_code == 200
    assert response.json() == {"answer": "42"}


def test_ask_rejects_empty_question() -> None:
    assert client.post("/ask", json={"question": ""}).status_code == 422
