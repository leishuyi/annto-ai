from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name: str = "annto 供应链智能决策助手"
    app_env: str = "development"
    debug: bool = True
    api_key: str = ""
    mock_mode: bool = True
    llm_api_key: str = ""
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ANNTO_")
settings = Settings()
