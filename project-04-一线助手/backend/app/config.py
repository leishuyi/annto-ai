from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "annto 一线人员智能助手"
    app_env: str = "development"
    debug: bool = True
    api_key: str = ""
    mock_mode: bool = True
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ANNTO_")


settings = Settings()
