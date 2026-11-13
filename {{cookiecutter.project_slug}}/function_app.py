"""Azure Functions entry point (v2 programming model)."""

import json

import azure.functions as func

from {{ cookiecutter.package_name }}.service import answer

_MAX_QUESTION_CHARS = 4000

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def _json(body: dict[str, str], status_code: int) -> func.HttpResponse:
    return func.HttpResponse(json.dumps(body), status_code=status_code, mimetype="application/json")


@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
# The HTTP trigger binds the request by parameter name, so `req` stays even though it is unused.
def health(req: func.HttpRequest) -> func.HttpResponse:  # pylint: disable=unused-argument
    """Liveness probe."""
    return _json({"status": "ok"}, 200)


@app.route(route="ask", methods=["POST"])
async def ask(req: func.HttpRequest) -> func.HttpResponse:
    """Answer the `question` field of a JSON body."""
    try:
        body = req.get_json()
    except ValueError:
        return _json({"error": "Body must be JSON."}, 400)
    question = body.get("question") if isinstance(body, dict) else None
    if not isinstance(question, str) or not 0 < len(question) <= _MAX_QUESTION_CHARS:
        return _json({"error": f"'question' must be a string of 1-{_MAX_QUESTION_CHARS} characters."}, 400)
    return _json({"answer": await answer(question)}, 200)
