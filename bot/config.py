import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    bot_token: str
    manager_id: int | None


class ConfigError(Exception):
    pass


def load_config() -> Config:
    load_dotenv(PROJECT_ROOT / ".env")

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise ConfigError(
            "Не задан TELEGRAM_BOT_TOKEN в файле .env. "
            "Получите токен у @BotFather и вставьте его после знака =."
        )

    manager_raw = os.getenv("MANAGER_TELEGRAM_ID", "").strip()
    manager_id = int(manager_raw) if manager_raw.isdigit() else None

    return Config(bot_token=token, manager_id=manager_id)
