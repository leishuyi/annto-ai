from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "annto A2A 智能客服平台"
    debug: bool = True
    app_env: str = "development"
    database_url: str = "sqlite:///./annto.db"
    upload_dir: str = str(Path(__file__).parent.parent.parent / "data" / "uploads")
    feature_human_gate: bool = True
    feature_risk_control: bool = True
    feature_audit_log: bool = True
    feature_agent_parallel: bool = False  # 默认关闭并行：当前 Agent 间存在隐式数据依赖（如 B 的输出被 C 和 D 共用），启用前需验证无竞态
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

    def check_security(self):
        """启动时校验安全配置"""
        if self.is_production() and not self.api_key:
            raise ValueError("生产环境必须设置 ANNTO_API_KEY")
        if self.is_production() and self.debug:
            raise ValueError("生产环境必须设置 debug=False")
        # 确保 upload_dir 存在（StaticFiles 在 lifespan 之前执行，必须提前创建）
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.check_security()
    return s


settings = get_settings()
