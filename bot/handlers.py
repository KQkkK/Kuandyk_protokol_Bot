from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Здравствуйте! Бот поручений работает.\n\n"
        f"Ваш Telegram ID: {message.from_user.id}\n"
        "Он понадобится, чтобы бот узнавал руководителя."
    )
