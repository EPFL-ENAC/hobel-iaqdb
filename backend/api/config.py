from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):

    # Postgres settings
    DB_HOST: str
    DB_PORT: int  # 5432
    DB_USER: str
    DB_PASSWORD: str

    DB_NAME: str  # postgres
    DB_PREFIX: str = "postgresql+asyncpg"

    DB_URL: str | None = None

    # Keycloak
    KEYCLOAK_REALM: str = "HOBEL"
    KEYCLOAK_URL: str = "https://enac-it-sso.epfl.ch"
    KEYCLOAK_API_ID: str
    KEYCLOAK_API_SECRET: str

    PATH_PREFIX: str = "/api"

    ELEVATION_URL: str = "https://api.open-elevation.com/api/v1/lookup"

    S3_ENDPOINT_PROTOCOL: str
    S3_ENDPOINT_HOSTNAME: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_REGION: str
    S3_BUCKET: str
    S3_PATH_PREFIX: str

    # Public URL of the app, for the links sent by email
    APP_URL: str = "http://localhost:8000"

    # Explore downloads
    DOWNLOAD_MAX_RECORDS: int = 200_000_000
    # running download jobs across all backend pods
    DOWNLOAD_MAX_CONCURRENT: int = 2
    DOWNLOAD_TMP_DIR: str | None = None  # system temp dir when unset

    # SMTP relay; when SMTP_HOST is empty, emails are logged instead of sent
    SMTP_HOST: str = "mail.epfl.ch"
    SMTP_PORT: int = 25
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "noreply+iaqdb@epfl.ch"
    SMTP_STARTTLS: bool = True

    @model_validator(mode="before")
    def form_db_url(cls, values: dict) -> dict:
        """Form the DB URL from the settings"""
        if "DB_URL" not in values:
            values["DB_URL"] = "{prefix}://{user}:{password}@{host}:{port}/{db}".format(
                prefix=values["DB_PREFIX"],
                user=values["DB_USER"],
                password=values["DB_PASSWORD"],
                host=values["DB_HOST"],
                port=values["DB_PORT"],
                db=values["DB_NAME"],
            )
        return values


@lru_cache()
def get_config():
    return Config()


config = get_config()
