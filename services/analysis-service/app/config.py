from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore',
        case_sensitive=False,
    )

    # Postgres
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = 'postgres'
    postgres_port: int = 5432
    
    # Services
    passenger_service_url: str = 'http://passenger-service:8002'

    # JWT (общий секрет с auth-service)
    jwt_secret_key: str
    jwt_algorithm: str = 'HS256'

    # ML
    sentence_transformer_model: str = 'all-MiniLM-L6-v2'
    kmeans_n_clusters: int = 5


    @property
    def database_url(self) -> str:
        return (
            f'postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}'
            f'@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}'
        )


settings = Settings()