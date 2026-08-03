import pytest


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    """Ensure Settings() can be instantiated in tests without a real .env file."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
