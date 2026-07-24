from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name: str = "annto 供应链智能决策助手"
    debug: bool = True
    mock_mode: bool = True
    llm_api_key: str = ""
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ANNTO_")
settings = Settings()
