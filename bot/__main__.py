import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher

from . import db, groups, onboarding, setup_mode
from .config import ConfigError, load_config


async def main() -> None:
    config = load_config()
    db.init_db()

    bot = Bot(config.bot_token)
    dp = Dispatcher(config=config)
    if config.manager_id is None:
        dp.include_router(setup_mode.router)
    else:
        dp.include_router(onboarding.router)
        dp.include_router(groups.router)

    me = await bot.get_me()
    logging.info("Бот @%s запущен. Остановить: Ctrl+C", me.username)
    if config.manager_id is None:
        logging.warning("Руководитель не указан (MANAGER_TELEGRAM_ID). Режим настройки.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    try:
        asyncio.run(main())
    except ConfigError as e:
        print(f"\nОшибка настройки: {e}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        pass
