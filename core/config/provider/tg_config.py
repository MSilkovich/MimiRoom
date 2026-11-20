from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TG_BOT_USERNAME: str


settings_tg = Settings()
