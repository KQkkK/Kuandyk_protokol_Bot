"""Подключение сотрудников: ссылка-приглашение → имя → подтверждение руководителя."""

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from . import db
from .config import Config
from .filters import IsManager

router = Router()
router.message.filter(F.chat.type == "private")

MAX_NAME_LENGTH = 60


class EmployeeAction(CallbackData, prefix="emp"):
    action: str  # approve | reject | remove
    telegram_id: int


async def invite_link(bot: Bot) -> str:
    me = await bot.me()
    return f"https://t.me/{me.username}?start=join"


def describe(employee) -> str:
    name = employee["full_name"] or "Без имени"
    return f"{name} (@{employee['username']})" if employee["username"] else name


# --- Руководитель ---

@router.message(CommandStart(), IsManager())
async def manager_start(message: Message, bot: Bot) -> None:
    await message.answer(
        "Здравствуйте! Вы руководитель.\n\n"
        "Ссылка для сотрудников — перешлите её им:\n"
        f"{await invite_link(bot)}\n\n"
        "Команды:\n"
        "/staff — сотрудники\n"
        "/groups — группы для общих поручений"
    )


@router.message(Command("staff"), IsManager())
async def staff_list(message: Message, bot: Bot) -> None:
    pending = db.list_employees("pending")
    active = db.list_employees("active")

    if not pending and not active:
        await message.answer(
            "Сотрудников пока нет. Перешлите им ссылку:\n" + await invite_link(bot)
        )
        return

    for employee in pending:
        await message.answer(
            f"⏳ Ждёт подтверждения: {describe(employee)}",
            reply_markup=approval_keyboard(employee["telegram_id"]),
        )

    if active:
        buttons = [
            [InlineKeyboardButton(
                text=f"Отключить: {employee['full_name']}",
                callback_data=EmployeeAction(action="remove", telegram_id=employee["telegram_id"]).pack(),
            )]
            for employee in active
        ]
        lines = "\n".join(f"• {describe(e)}" for e in active)
        await message.answer(
            f"Подключены ({len(active)}):\n{lines}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )


def approval_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Подтвердить",
            callback_data=EmployeeAction(action="approve", telegram_id=telegram_id).pack(),
        ),
        InlineKeyboardButton(
            text="Отклонить",
            callback_data=EmployeeAction(action="reject", telegram_id=telegram_id).pack(),
        ),
    ]])


@router.callback_query(EmployeeAction.filter(), IsManager())
async def employee_decision(callback: CallbackQuery, callback_data: EmployeeAction, bot: Bot) -> None:
    tid = callback_data.telegram_id
    employee = db.get_employee(tid)
    if employee is None:
        await callback.answer("Сотрудник не найден.", show_alert=True)
        return

    who = describe(employee)

    if callback_data.action == "approve":
        if not db.change_employee_status(tid, "pending", "active"):
            await callback.answer("Уже решено ранее.")
            return
        await callback.message.edit_text(f"✅ {who} подключён(а).")
        await bot.send_message(tid, "Готово, вы подключены. Сюда будут приходить ваши поручения.")

    elif callback_data.action == "reject":
        if not db.change_employee_status(tid, "pending", "rejected"):
            await callback.answer("Уже решено ранее.")
            return
        await callback.message.edit_text(f"Отклонено: {who}.")
        await bot.send_message(tid, "Доступ не подтверждён. Обратитесь к руководителю.")

    elif callback_data.action == "remove":
        if not db.change_employee_status(tid, "active", "removed"):
            await callback.answer("Сотрудник уже отключён.")
            return
        await callback.message.answer(f"Отключён(а): {who}.")
        await bot.send_message(tid, "Доступ к боту поручений закрыт руководителем.")

    await callback.answer()


@router.callback_query(EmployeeAction.filter())
async def employee_decision_forbidden(callback: CallbackQuery) -> None:
    await callback.answer("Это может сделать только руководитель.", show_alert=True)


# --- Сотрудник ---

@router.message(CommandStart())
async def employee_start(message: Message) -> None:
    user = message.from_user
    employee = db.get_employee(user.id)
    status = employee["status"] if employee else None

    if status == "active":
        await message.answer("Вы уже подключены. Сюда будут приходить ваши поручения.")
    elif status == "pending":
        await message.answer("Спасибо. Ждём подтверждения руководителя.")
    elif status == "rejected":
        await message.answer("Доступ не подтверждён. Обратитесь к руководителю.")
    else:
        db.start_registration(user.id, user.username)
        await message.answer("Здравствуйте! Как вас зовут? Напишите имя и фамилию.")


@router.message(F.text, ~F.text.startswith("/"), ~IsManager())
async def employee_text(message: Message, bot: Bot, config: Config) -> None:
    employee = db.get_employee(message.from_user.id)

    if employee is None:
        await message.answer("Чтобы подключиться, нажмите /start.")
        return

    if employee["status"] != "awaiting_name":
        await message.answer(
            "Поручения приходят сюда автоматически. "
            "Ответить на поручение можно кнопками под ним."
        )
        return

    name = " ".join(message.text.split())
    if len(name) < 2 or len(name) > MAX_NAME_LENGTH:
        await message.answer(f"Напишите имя и фамилию — от 2 до {MAX_NAME_LENGTH} символов.")
        return

    db.submit_name(message.from_user.id, name)
    await message.answer("Спасибо. Ждём подтверждения руководителя.")

    await bot.send_message(
        config.manager_id,
        f"Новый сотрудник в боте: {describe(db.get_employee(message.from_user.id))}. Это ваш сотрудник?",
        reply_markup=approval_keyboard(message.from_user.id),
    )
