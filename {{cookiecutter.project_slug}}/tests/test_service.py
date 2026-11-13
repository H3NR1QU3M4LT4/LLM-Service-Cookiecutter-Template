from unittest.mock import AsyncMock, patch

from ai_utils.llm import TextResponse

from {{ cookiecutter.package_name }} import service


async def test_answer_returns_model_answer_with_system_message() -> None:
    complete = AsyncMock(return_value=TextResponse(answer="42"))
    with patch.object(service.get_llm_client(), "complete", new=complete):
        assert await service.answer("Meaning of life?") == "42"

    assert complete.call_args.kwargs["system_message"] == service.SYSTEM_MESSAGE
