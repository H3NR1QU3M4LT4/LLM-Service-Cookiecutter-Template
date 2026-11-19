"""Versioned prompt files, loaded from `src/prompts/*.yaml`."""

from dataclasses import dataclass
from pathlib import Path

import yaml
from semantic_kernel.prompt_template import PromptTemplateConfig

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@dataclass(frozen=True)
class Prompt:
    """A prompt template and the version recorded in its file."""

    name: str
    version: str
    config: PromptTemplateConfig


def parse_prompt(text: str) -> Prompt:
    """Parse the text of a prompt YAML file.

    Args:
        text: File content (for example from `git show <ref>:<path>`).

    Returns:
        The prompt with its version.
    """
    data = yaml.safe_load(text)
    version = str(data.pop("version"))
    return Prompt(name=data["name"], version=version, config=PromptTemplateConfig(**data))


def load_prompt(name: str, directory: Path = _PROMPTS_DIR) -> Prompt:
    """Load `<directory>/<name>.yaml`.

    Args:
        name: File name without extension.
        directory: Folder with the prompt files; defaults to `src/prompts`.

    Returns:
        The prompt with its version.
    """
    return parse_prompt((directory / f"{name}.yaml").read_text(encoding="utf-8"))
