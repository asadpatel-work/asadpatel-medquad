"""Unit tests for configuration loading."""

from backend.core.config import Settings, get_settings


def test_default_settings():
    """Verify that default settings instantiate with expected properties."""
    settings = Settings(_env_file=None)
    assert isinstance(settings, Settings)
    assert settings.app_name == "MedQuAD Clinical Assistant"
    assert settings.root_orchestrator_model == "gemini-2.5-flash"
    assert settings.researcher_model == "gemini-2.5-pro"
    assert settings.reviewer_model == "gemini-3.5-flash"
    assert isinstance(settings.use_mock_search, bool)
