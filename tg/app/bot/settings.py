from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    dev: bool = False
    test_server: bool = False
    developer_id: int
    webhooks: bool = False
    bot_token: SecretStr
    webhook_url: SecretStr
    webhook_secret_token: SecretStr
