from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "智家能"
    app_env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"

    database_url: str = "sqlite:///data/smart_energy.db"

    demo_user_id: int = 1
    demo_date: str = "2026-08-19"
    random_seed: int = 42
    city: str = "成都"
    season: str = "夏季"
    data_mode: str = "demo"

    price_peak: float = 0.72
    price_flat: float = 0.52
    price_valley: float = 0.28
    carbon_kg_per_kwh: float = 0.525

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def resolved_database_url(self) -> str:
        url = self.database_url
        sqlite_prefix = "sqlite:///"
        if url.startswith(sqlite_prefix) and not url.startswith("sqlite:////"):
            raw_path = url[len(sqlite_prefix) :]
            db_path = Path(raw_path)
            if not db_path.is_absolute():
                db_path = PROJECT_ROOT / db_path
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{db_path.as_posix()}"
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
