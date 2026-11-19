import hashlib

import pytest

from llm.prompts import load_prompt

# prompt name -> (version, sha256 of its template). Changing a template fails this test until the version in the
# YAML file is bumped and the entry below is updated, so prompt changes are always an explicit, reviewed diff.
PINNED = {"ask": ("1.1.0", "7d858d54720b13f0e61e9f44c2af41b5c9015697ec7cae4b7bdd5c63c1b94909")}


@pytest.mark.parametrize("name", PINNED)
def test_prompt_change_requires_version_bump(name: str) -> None:
    prompt = load_prompt(name)
    digest = hashlib.sha256((prompt.config.template or "").encode()).hexdigest()
    assert (prompt.version, digest) == (PINNED[name][0], PINNED[name][1]), (
        f"Prompt {name!r} changed: bump `version` in src/prompts/{name}.yaml and update PINNED "
        f"to ({prompt.version!r}, {digest!r})."
    )
