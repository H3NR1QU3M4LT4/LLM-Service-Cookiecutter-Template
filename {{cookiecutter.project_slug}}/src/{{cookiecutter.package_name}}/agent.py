"""Microsoft Foundry prompt agent with a local function tool and optional Azure AI Search grounding.

Uses `azure-ai-projects` 2.x: agents are versioned server-side and called through the project's
OpenAI-compatible Responses API. Function tools run here, in this process: the agent returns
`function_call` items and we send back `function_call_output` items until it produces text.

Usage:
    python -m {{ cookiecutter.package_name }}.agent deploy          # create a version and route traffic to it
    python -m {{ cookiecutter.package_name }}.agent ask "question"  # ask the deployed agent
"""

import json
import os
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentEndpointConfig,
    AISearchIndexResource,
    AzureAISearchQueryType,
    AzureAISearchTool,
    AzureAISearchToolResource,
    FixedRatioVersionSelectionRule,
    FunctionTool,
    PromptAgentDefinition,
    ProtocolConfiguration,
    ResponsesProtocolConfiguration,
    Tool,
    VersionSelector,
)
from azure.identity import DefaultAzureCredential
from openai import OpenAI
from openai.types.responses.response_input_param import FunctionCallOutput, ResponseInputParam

AGENT_NAME = "{{ cookiecutter.project_slug }}-agent"
INSTRUCTIONS = (
    "You are a helpful assistant. Use the search tool for questions about the indexed documents and cite "
    "the sources you used. Use get_current_utc_time for anything that depends on today's date."
)
_MAX_TOOL_ROUNDS = 5


def get_current_utc_time() -> str:
    """Example function tool: return the current UTC time in ISO 8601."""
    return datetime.now(UTC).isoformat(timespec="seconds")


# Function tools the agent may call, by name. Add yours here and in `build_tools`.
FUNCTIONS: dict[str, Callable[..., str]] = {"get_current_utc_time": get_current_utc_time}


def build_tools() -> list[Tool]:
    """Declare the agent's tools; Azure AI Search is added when its connection is configured."""
    tools: list[Tool] = [
        FunctionTool(
            name="get_current_utc_time",
            description="Get the current date and time in UTC.",
            parameters={"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            strict=True,
        )
    ]
    connection_id = os.environ.get("AI_SEARCH_PROJECT_CONNECTION_ID")
    if connection_id:
        index = AISearchIndexResource(
            project_connection_id=connection_id,
            index_name=os.environ["AI_SEARCH_INDEX_NAME"],
            query_type=AzureAISearchQueryType.VECTOR_SEMANTIC_HYBRID,
        )
        tools.append(AzureAISearchTool(azure_ai_search=AzureAISearchToolResource(indexes=[index])))
    return tools


def get_project_client() -> AIProjectClient:
    """Create a Foundry project client (Entra ID is the only auth the service accepts)."""
    return AIProjectClient(endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())


def deploy_agent(project: AIProjectClient) -> str:
    """Create a new agent version and route 100% of the agent endpoint's traffic to it.

    Args:
        project: Foundry project client.

    Returns:
        The new version identifier.
    """
    version = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=os.environ["FOUNDRY_MODEL_NAME"], instructions=INSTRUCTIONS, tools=build_tools()
        ),
    )
    project.agents.update_details(
        agent_name=AGENT_NAME,
        agent_endpoint=AgentEndpointConfig(
            version_selector=VersionSelector(
                version_selection_rules=[
                    FixedRatioVersionSelectionRule(agent_version=version.version, traffic_percentage=100)
                ]
            ),
            protocol_configuration=ProtocolConfiguration(responses=ResponsesProtocolConfiguration()),
        ),
    )
    return version.version


def _call_function(name: str, arguments: str) -> str:
    """Run a function tool requested by the agent, reporting failures back to it instead of crashing."""
    function = FUNCTIONS.get(name)
    if function is None:
        return json.dumps({"error": f"Unknown function {name!r}."})
    try:
        kwargs: dict[str, Any] = json.loads(arguments or "{}")
        return json.dumps({"result": function(**kwargs)})
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})


def ask(openai_client: OpenAI, question: str, max_tool_rounds: int = _MAX_TOOL_ROUNDS) -> str:
    """Ask the agent a question, executing function-tool calls until it answers in text.

    Args:
        openai_client: Client from `project.get_openai_client(agent_name=AGENT_NAME)`.
        question: The user's question.
        max_tool_rounds: Upper bound on function-call round trips, so a looping agent cannot run forever.

    Returns:
        The agent's final text answer.

    Raises:
        RuntimeError: If the agent is still calling tools after `max_tool_rounds` rounds.
    """
    response = openai_client.responses.create(input=question)
    for _ in range(max_tool_rounds):
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return response.output_text
        outputs: ResponseInputParam = [
            FunctionCallOutput(
                type="function_call_output", call_id=call.call_id, output=_call_function(call.name, call.arguments)
            )
            for call in calls
        ]
        response = openai_client.responses.create(input=outputs, previous_response_id=response.id)
    raise RuntimeError(f"Agent still calling tools after {max_tool_rounds} rounds.")


def main(argv: list[str]) -> None:
    """CLI: `deploy` or `ask <question>`."""
    with get_project_client() as project:
        if argv[:1] == ["deploy"]:
            print(f"Deployed {AGENT_NAME} version {deploy_agent(project)}")
        elif argv[:1] == ["ask"] and len(argv) > 1:
            with project.get_openai_client(agent_name=AGENT_NAME) as openai_client:
                print(ask(openai_client, " ".join(argv[1:])))
        else:
            sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
