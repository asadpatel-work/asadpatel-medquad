"""Configuration management for MedQuAD Clinical Assistant."""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application Settings
    app_name: str = "MedQuAD Clinical Assistant"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # API Keys & Auth
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")

    # GCP Infrastructure
    gcp_project_id: str = "capstone-506616"
    gcp_region: str = "us-central1"
    medquad_gcs_bucket: str = "gs://capstone-506616-medquad-corpus"

    # Vertex AI Search (Discovery Engine)
    vertex_ai_search_datastore_id: str = Field(
        default="medquad-corpus-v1",
        validation_alias=AliasChoices(
            "VERTEX_AI_SEARCH_DATASTORE_ID",
            "VERTEX_DATASTORE_ID",
            "DATASTORE_ID",
        ),
    )
    vertex_ai_search_engine_id: str = Field(
        default="medquad-search-app-v2",
        validation_alias=AliasChoices(
            "VERTEX_AI_SEARCH_ENGINE_ID",
            "VERTEX_ENGINE_ID",
            "ENGINE_ID",
        ),
    )
    vertex_ai_search_location: str = "global"
    use_mock_search: bool = False
    medquad_corpus_path: str = Field(
        default="data/full_medquad.json",
        validation_alias=AliasChoices("MEDQUAD_CORPUS_PATH", "CORPUS_PATH"),
    )

    # Multi-Agent Models
    root_orchestrator_model: str = "gemini-2.5-flash"
    gemini_orchestrator_model: str = "gemini-2.5-flash"

    researcher_model: str = "gemini-2.5-pro"
    gemini_researcher_model: str = "gemini-2.5-pro"

    reviewer_model: str = "gemini-3.5-flash"
    gemini_reviewer_model: str = "gemini-3.5-flash"

    # Safety Guardrails
    enable_model_armor: bool = True
    strict_safe_refusal: bool = True

    # Observability
    enable_opentelemetry: bool = True
    export_to_cloud_trace: bool = False
    bigquery_telemetry_table: str = "capstone-506616.telemetry.agent_metrics"

    # Automated Nightly Clinical Conversation Auditing
    enable_nightly_audit_scheduler: bool = True
    nightly_audit_hour_utc: int = 0  # 00:00 UTC (midnight)


@lru_cache
def get_settings() -> Settings:
    """Returns cached instance of the application settings."""
    return Settings()
