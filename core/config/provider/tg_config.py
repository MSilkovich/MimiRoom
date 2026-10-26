from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TG_BOT_USERNAME: str

    class Config:
        env_file = ".env"


settings_tg = Settings()
