import json
from unittest.mock import AsyncMock, patch

import azure.functions as func
import pytest

import function_app


def _request(body: bytes) -> func.HttpRequest:
    return func.HttpRequest(method="POST", url="/api/ask", body=body)


async def test_ask_returns_answer() -> None:
    with patch("function_app.answer", new=AsyncMock(return_value="42")):
        response = await function_app.ask(_request(json.dumps({"question": "Meaning of life?"}).encode()))

    assert response.status_code == 200
    assert json.loads(response.get_body()) == {"answer": "42"}


@pytest.mark.parametrize("body", [b"not json", b"[1, 2]", b'{"question": ""}', b'{"question": 5}'])
async def test_ask_rejects_bad_bodies(body: bytes) -> None:
    response = await function_app.ask(_request(body))

    assert response.status_code == 400
