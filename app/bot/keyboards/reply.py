from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def digest_days() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for item in [str(i) for i in range(1, 8)]:
        builder.button(text=item)
    builder.button(text="Назад")
    builder.adjust(7, 1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def skip_filter() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Назад")
    builder.button(text="Пропустить")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def back_button() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Назад")
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)