import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher

from .config import ConfigError, load_config
from .handlers import router


async def main() -> None:
    config = load_config()
    bot = Bot(config.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    me = await bot.get_me()
    logging.info("Бот @%s запущен. Остановить: Ctrl+C", me.username)
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
