import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from {{ cookiecutter.package_name }} import agent


def _response(response_id: str, output: list[SimpleNamespace], text: str = "") -> SimpleNamespace:
    return SimpleNamespace(id=response_id, output=output, output_text=text)


def _function_call(name: str, arguments: str = "{}") -> SimpleNamespace:
    return SimpleNamespace(type="function_call", name=name, arguments=arguments, call_id=f"call-{name}")


def test_ask_runs_function_tools_then_returns_text() -> None:
    client = MagicMock()
    client.responses.create.side_effect = [
        _response("r1", [_function_call("get_current_utc_time")]),
        _response("r2", [SimpleNamespace(type="message")], text="It is noon."),
    ]

    assert agent.ask(client, "What time is it?") == "It is noon."

    second = client.responses.create.call_args_list[1].kwargs
    assert second["previous_response_id"] == "r1"
    [output] = second["input"]
    assert output["call_id"] == "call-get_current_utc_time"
    assert "result" in json.loads(output["output"])


def test_unknown_function_is_reported_to_the_agent() -> None:
    assert "Unknown function" in json.loads(agent._call_function("rm_rf", "{}"))["error"]


def test_bad_arguments_are_reported_to_the_agent() -> None:
    assert "TypeError" in json.loads(agent._call_function("get_current_utc_time", '{"x": 1}'))["error"]


def test_ask_stops_after_max_tool_rounds() -> None:
    client = MagicMock()
    client.responses.create.return_value = _response("r", [_function_call("get_current_utc_time")])

    with pytest.raises(RuntimeError, match="2 rounds"):
        agent.ask(client, "loop", max_tool_rounds=2)


def test_search_tool_added_only_when_connection_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_SEARCH_PROJECT_CONNECTION_ID", raising=False)
    assert len(agent.build_tools()) == 1

    monkeypatch.setenv("AI_SEARCH_PROJECT_CONNECTION_ID", "conn")
    monkeypatch.setenv("AI_SEARCH_INDEX_NAME", "docs")
    assert [tool.type for tool in agent.build_tools()] == ["function", "azure_ai_search"]
