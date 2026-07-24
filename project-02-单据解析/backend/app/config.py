from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "annto 多模态物流单据解析引擎"
    app_env: str = "development"
    debug: bool = True
    api_key: str = ""
    supported_doc_types: list[str] = ["waybill", "receipt", "warehouse_doc", "invoice", "id_document"]
    ocr_provider: str = "mock"
    llm_provider: str = "mock"
    upload_dir: str = "data/uploads"
    max_upload_size: int = 10 * 1024 * 1024
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ANNTO_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
