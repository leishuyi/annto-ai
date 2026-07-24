from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name: str = "annto 多模态物流单据解析引擎"
    debug: bool = True
    supported_doc_types: list[str] = ["waybill", "receipt", "warehouse_doc", "invoice", "id_document"]
    ocr_provider: str = "mock"
    llm_provider: str = "mock"
    upload_dir: str = "data/uploads"
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ANNTO_")
settings = Settings()
