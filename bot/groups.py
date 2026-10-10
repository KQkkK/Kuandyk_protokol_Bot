"""Группы для общих поручений: подключаются, только если бота добавил руководитель
или руководитель подтвердил."""

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup, Message

from . import db
from .config import Config
from .filters import IsManager

router = Router()

IN_CHAT = {"member", "administrator"}
OUT_OF_CHAT = {"left", "kicked"}


class GroupAction(CallbackData, prefix="grp"):
    action: str  # approve | reject
    chat_id: int


@router.my_chat_member(F.chat.type.in_({"group", "supergroup"}))
async def bot_membership_changed(event: ChatMemberUpdated, bot: Bot, config: Config) -> None:
    chat = event.chat
    new_status = event.new_chat_member.status

    if new_status in OUT_OF_CHAT:
        group = db.get_group(chat.id)
        if group and group["status"] != "removed":
            db.save_group(chat.id, chat.title, "removed")
            await bot.send_message(
                config.manager_id, f"Бота убрали из группы «{chat.title}». Общие поручения туда больше не уходят."
            )
        return

    if new_status not in IN_CHAT:
        return

    if event.from_user.id == config.manager_id:
        db.save_group(chat.id, chat.title, "active")
        await bot.send_message(config.manager_id, f"Группа «{chat.title}» подключена для общих поручений.")
        return

    db.save_group(chat.id, chat.title, "pending")
    who = event.from_user.full_name
    await bot.send_message(
        config.manager_id,
        f"{who} добавил(а) бота в группу «{chat.title}». Разрешить отправлять туда общие поручения?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="Разрешить", callback_data=GroupAction(action="approve", chat_id=chat.id).pack()
            ),
            InlineKeyboardButton(
                text="Запретить", callback_data=GroupAction(action="reject", chat_id=chat.id).pack()
            ),
        ]]),
    )


@router.callback_query(GroupAction.filter(), IsManager())
async def group_decision(callback: CallbackQuery, callback_data: GroupAction, bot: Bot) -> None:
    group = db.get_group(callback_data.chat_id)
    if group is None:
        await callback.answer("Группа не найдена.", show_alert=True)
        return

    if callback_data.action == "approve":
        if not db.change_group_status(group["chat_id"], "pending", "active"):
            await callback.answer("Уже решено ранее.")
            return
        await callback.message.edit_text(f"Группа «{group['title']}» подключена для общих поручений.")
    else:
        if not db.change_group_status(group["chat_id"], "pending", "rejected"):
            await callback.answer("Уже решено ранее.")
            return
        await callback.message.edit_text(f"Группа «{group['title']}» не подключена. Бот из неё вышел.")
        await bot.leave_chat(group["chat_id"])

    await callback.answer()


@router.message(Command("groups"), IsManager(), F.chat.type == "private")
async def groups_list(message: Message) -> None:
    groups = db.list_groups("active")
    if not groups:
        await message.answer(
            "Групп пока нет. Добавьте бота в нужную группу Telegram — "
            "она подключится автоматически, раз добавляете вы."
        )
        return
    lines = "\n".join(f"• {g['title']}" for g in groups)
    await message.answer(f"Группы для общих поручений ({len(groups)}):\n{lines}")
