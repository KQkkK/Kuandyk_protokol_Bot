"""Режим настройки: руководитель ещё не указан, бот только сообщает людям их ID."""

from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message()
async def show_id(message: Message) -> None:
    await message.answer(
        "Бот в режиме настройки.\n\n"
        f"Ваш Telegram ID: {message.from_user.id}\n\n"
        "Если вы руководитель — впишите это число в файл .env "
        "в строку MANAGER_TELEGRAM_ID= и перезапустите бота."
    )
