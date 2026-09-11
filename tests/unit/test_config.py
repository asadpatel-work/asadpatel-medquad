"""Unit tests for configuration loading."""

from backend.core.config import Settings


def test_default_settings():
    """Verify that default settings instantiate with expected properties."""
    settings = Settings(_env_file=None)
    assert isinstance(settings, Settings)
    assert settings.app_name == "MedQuAD Clinical Assistant"
    assert settings.root_orchestrator_model == "gemini-2.5-flash"
    assert settings.researcher_model == "gemini-2.5-pro"
    assert settings.reviewer_model == "gemini-3.5-flash"
    assert isinstance(settings.use_mock_search, bool)
    assert "https://medquad-frontend-dhwfxdn3vq-uc.a.run.app" in settings.cors_allowed_origins
    assert "http://localhost:3000" in settings.cors_allowed_origins


def test_cors_origins_parsing():
    """Verify that CORS origins can be parsed from comma-separated string or JSON list."""
    # Comma-separated
    s1 = Settings(_env_file=None, ALLOWED_ORIGINS="https://app.example.com, https://portal.example.com")
    assert s1.cors_allowed_origins == ["https://app.example.com", "https://portal.example.com"]

    # JSON list
    s2 = Settings(_env_file=None, ALLOWED_ORIGINS='["https://app2.example.com", "http://localhost:8080"]')
    assert s2.cors_allowed_origins == ["https://app2.example.com", "http://localhost:8080"]
