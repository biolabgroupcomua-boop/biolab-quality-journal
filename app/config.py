from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Налаштування застосунку. Читаються з .env або змінних середовища."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # шляхи (відносно кореня репо)
    project_root: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = project_root / "data"
    passports_dir: Path = data_dir / "passports"
    backups_dir: Path = data_dir / "backups"

    # БД
    database_url: str = f"sqlite:///{data_dir / 'journal.db'}"

    # google sheet — джерело для імпорту і ціль для дзеркала
    source_sheet_id: str = "1aZl3uuEYQm2VGF1-6w7RF_IaubOpHS7gkrmxUZc2bE8"
    service_account_path: Path = project_root / "credentials" / "service_account.json"

    # шаблон паспорта
    passport_template_path: Path = project_root / "app" / "templates" / "passport.html.j2"

    # сервер
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()

# гарантуємо що теки існують при старті
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.passports_dir.mkdir(parents=True, exist_ok=True)
settings.backups_dir.mkdir(parents=True, exist_ok=True)
