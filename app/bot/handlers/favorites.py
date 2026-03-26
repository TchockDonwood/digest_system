import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.favorite_digest import FavoriteDigestDAO
from app.dao.digest import DigestDAO
from app.dao.cluster import ClusterDAO
from app.database.models.user import User
from app.config import settings

router = Router()

@router.callback_query(F.data == "menu_favorites")
async def show_favorites(callback: CallbackQuery, session: AsyncSession, user: User):
    """Показывает список избранных дайджестов (только заголовки) с кнопками для просмотра и удаления."""
    fav_dao = FavoriteDigestDAO(session)
    digest_dao = DigestDAO(session)

    # Получаем все избранные записи пользователя
    favorites = await fav_dao.get_user_favorite_digests(user.id)  # предполагается, что возвращает список Digest
    if not favorites:
        await callback.answer("У вас нет избранных дайджестов")
        return

    # Сортируем по дате (новые сверху)
    favorites.sort(key=lambda d: d.created_at, reverse=True)

    # Формируем клавиатуру: каждая пара кнопок — просмотр и удаление
    keyboard = []
    for digest in favorites:
        title = digest.title or "Без названия"
        date_str = digest.created_at.strftime("%d.%m.%Y")
        button_text = f"{title} ({date_str})"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"fav_view_{digest.id}")])
        keyboard.append([InlineKeyboardButton(text="❌ Удалить из избранного", callback_data=f"fav_remove_{digest.id}")])

    # Кнопка "Назад" в меню
    keyboard.append([InlineKeyboardButton(text="◀️ В меню", callback_data="menu_main")])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await callback.message.edit_text(
        "⭐ <b>Избранные дайджесты</b>\n\nВыберите дайджест для просмотра или удаления:",
        reply_markup=markup,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fav_view_"))
async def view_favorite_digest(callback: CallbackQuery, session: AsyncSession, user: User):
    """Отправляет полный дайджест (кластеры, аудио) по выбранному digest_id."""
    digest_id_str = callback.data.split("_")[-1]
    digest_dao = DigestDAO(session)
    cluster_dao = ClusterDAO(session)

    # Получаем дайджест
    try:
        digest = await digest_dao.get_by_id(digest_id_str)
    except:
        await callback.answer("Дайджест не найден")
        return

    if not digest or digest.user_id != user.id:
        await callback.answer("Дайджест не найден")
        return

    # Проверяем, действительно ли дайджест в избранном (для безопасности)
    fav_dao = FavoriteDigestDAO(session)
    fav = await fav_dao.get_one_or_none(user_id=user.id, digest_id=digest.id)
    if not fav:
        await callback.answer("Дайджест не в избранном")
        return

    # Получаем кластеры
    clusters = await cluster_dao.get_all(digest_id=digest.id)
    if not clusters:
        await callback.answer("Дайджест пуст")
        return

    bot = Bot(token=settings.BOT_TOKEN)

    try:
        # Приветственное сообщение
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="📰 *Ваш дайджест*",
            parse_mode="Markdown"
        )

        # Отправляем кластеры
        for cluster in clusters:
            if cluster.title and cluster.summary_text:
                message_text = f"📌 *{cluster.title}*\n\n{cluster.summary_text}"
                if len(message_text) > 4096:
                    message_text = message_text[:4000] + "...\n(обрезано)"
                await bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=message_text,
                    parse_mode="Markdown"
                )
                await asyncio.sleep(0.5)

        # Кнопки: удалить из избранного и в меню
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Удалить из избранного", callback_data=f"fav_remove_{digest.id}")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="menu_main")]
        ])
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="Вы можете удалить этот дайджест из избранного или вернуться в меню:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        # Аудио, если есть
        if digest.audio_path:
            import os
            if os.path.exists(digest.audio_path):
                with open(digest.audio_path, 'rb') as audio_file:
                    await bot.send_audio(
                        chat_id=callback.message.chat.id,
                        audio=audio_file,
                        caption="🎧 Аудио-версия дайджеста"
                    )
    except Exception as e:
        await callback.answer("Ошибка при отправке дайджеста")
        print(f"Error sending digest: {e}")
    finally:
        await bot.session.close()

    await callback.answer()


@router.callback_query(F.data.startswith("fav_remove_"))
async def remove_from_favorites(callback: CallbackQuery, session: AsyncSession, user: User):
    """Удаляет дайджест из избранного."""
    digest_id_str = callback.data.split("_")[-1]
    fav_dao = FavoriteDigestDAO(session)

    # Находим запись избранного
    fav = await fav_dao.get_one_or_none(user_id=user.id, digest_id=digest_id_str)
    if not fav:
        await callback.answer("Дайджест уже удалён из избранного")
        return

    # Удаляем
    await fav_dao.delete(id=fav.id)  # или fav_dao.delete(user_id=user.id, digest_id=digest_id_str)
    await session.commit()

    await callback.answer("Дайджест удалён из избранного")

    # Обновляем список избранного (перезапускаем show_favorites)
    await show_favorites(callback, session, user)