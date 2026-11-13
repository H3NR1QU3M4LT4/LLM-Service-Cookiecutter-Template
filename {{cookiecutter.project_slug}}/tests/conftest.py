import pytest


@pytest.fixture(autouse=True)
def azure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://fake.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "fake-deployment")
    monkeypatch.delenv("APPLICATION_INSIGHTS_CONNECTION_STRING", raising=False)
