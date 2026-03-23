from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    DATABASE_URL: str
    WEIGHT_MODEL_PATH: str
    STREAM_URL: str
    HOST_CAMERA: str
    PORT_CAMERA: int
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


configs = Config()

