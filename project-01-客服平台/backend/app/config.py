from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "annto A2A 智能客服平台"
    debug: bool = True
    app_env: str = "development"
    database_url: str = "sqlite:///./annto.db"
    upload_dir: str = "data/uploads"

    # ---- Feature Flags ----
    feature_human_gate: bool = True
    feature_risk_control: bool = True
    feature_audit_log: bool = True
    feature_agent_parallel: bool = False
    feature_event_bus: bool = True
    feature_rbac: bool = True

    # ---- 安全 ----
    api_key: str = ""
    pii_mask_enabled: bool = True
    api_rate_limit: str = "60/minute"

    # ---- 日志 ----
    log_level: str = "INFO"
    log_rotation: str = "500 MB"
    log_retention: str = "14 days"

    # ---- API ----
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list[str] = ["jpg", "jpeg", "png", "bmp", "tiff", "pdf"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",
                                      extra="ignore", case_sensitive=False, env_prefix="ANNTO_")

    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
