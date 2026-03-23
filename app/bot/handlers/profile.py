from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import main_menu, profile_menu
from app.dao.digest import DigestDAO
from app.dao.query_history import QueryHistoryDAO
from app.dao.subscription import SubscriptionDAO
from app.database.models.user import User

router = Router()

@router.callback_query(F.data == "menu_profile")
async def show_profile(callback: CallbackQuery, session: AsyncSession, user: User):
    # TODO: Получить тариф пользователя

    display_name = user.first_name or "Неизвестно"

    role_name = (
        "Администратор"
        if user.role.value == "ADMIN"
        else "Пользователь"
    )

    subscription_dao = SubscriptionDAO(session)
    subscription = await subscription_dao.get_one_or_none()
    subscription_name = "Отсутствует" if not subscription else subscription.name
    text = (
        "👤 <b>Личный кабинет</b>\n\n"
        f"<b>Имя:</b> {display_name}\n"
        f"<b>Роль:</b> {role_name}\n"
        f"<b>Тариф:</b> {subscription_name}\n"
        f"<b>Доступно токенов:</b> {user.token_balance}\n\n"
        f"<b>Дата регистрации:</b> {user.created_at.strftime('%d.%m.%Y')}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=profile_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "subsription_change")
async def change_subsription(callback: CallbackQuery):
    # TODO: Сделать хендлер для смены тарифа
    await callback.message.answer("Ваш тариф меняется...")
    await callback.answer()

@router.callback_query(F.data == "profile_history")
async def show_history(callback: CallbackQuery, session: AsyncSession, user: User):
    # TODO: переделать
    results = []

    history_dao = QueryHistoryDAO(session)
    digest_dao = DigestDAO(session)

    if await history_dao.get_one_or_none(user_id=user.id):
        queries = await history_dao.get_all(user_id=user.id)
    else:
        await callback.answer("История пуста")
        return

    digest_ids = [query.digest_id for query in queries]
    for digest_id in digest_ids:
        digest = await digest_dao.get_by_id(digest_id)
        results.append(
            f"<b>{digest.title}</b>\n\n"
            f"{digest.summary_text}\n"
            f"Дата создания: {digest.created_at.strftime('%d.%m.%Y')}\n\n"
            "-----------------------\n\n"
        )

    await callback.message.answer(''.join(results))
    await callback.answer(f"Найдено записей: {len(digest_ids)}")

@router.callback_query(F.data == "menu_main")
async def show_menu(callback: CallbackQuery, user: User):
    text = (
        "<b>Привет! Я твой персональный аналитик новостей.</b> 👋\n\n"
        "Я помогаю экономить время, превращая сотни сообщений из Telegram-каналов в краткие и структурированные дайджесты.\n\n"
        "<i>Воспользуйся меню ниже, чтобы настроить свои источники или создать первый дайджест.</i>"
    )
    await callback.message.edit_text(text, reply_markup=main_menu(user.role.value), parse_mode="HTML")
    await callback.answer()