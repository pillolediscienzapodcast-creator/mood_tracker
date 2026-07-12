from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    app_version: str
    debug: bool

    database_host: str
    database_port: int
    database_name: str
    database_user: str
    database_password: str

    # Privacy: se True, il testo dei turni viene memorizzato in chiaro nel
    # database; se False (default), si salvano solo feature ed esiti. Vedi
    # PRIVACY del prototipo: il testo grezzo e' un dato sensibile.
    store_turn_text: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


settings = Settings()
