from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PickleBuddy API"
    app_env: str = "development"
    app_debug: bool = True
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    allowed_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1):\d+$"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "secret"
    mysql_database: str = "picklebuddy"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
