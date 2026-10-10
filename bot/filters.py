from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from .config import Config


class IsManager(BaseFilter):
    """Пропускает только руководителя (ID из .env)."""

    async def __call__(self, event: Message | CallbackQuery, config: Config) -> bool:
        return event.from_user is not None and event.from_user.id == config.manager_id
