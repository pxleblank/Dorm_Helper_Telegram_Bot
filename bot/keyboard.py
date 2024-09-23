from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async

from complaints.models import Responsible
from users.models import User
from bot.config import admin_ids


def inline_keyboard_to_take_complain_with_id(complaint_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Взять жалобу", callback_data=f"take_complain:{complaint_id}"))
    return keyboard


async def get_complaint_keyboard(complaint_id):
    # Создаем клавиатуру для жалобы с кнопкой отмены
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("Отменить жалобу", callback_data=f"cancel_complaint:{complaint_id}"))
    return keyboard


# Функция для динамического формирования клавиатуры
async def get_user_keyboard(user_id):
    user = await sync_to_async(User.objects.filter)(telegram_id=user_id)
    user = await sync_to_async(user.first)()

    if user is None:
        # Если пользователь не зарегистрирован, отправляем клавиатуру для регистрации
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        register_button = KeyboardButton("Регистрация")
        keyboard.add(register_button)
        return keyboard

    if user.is_verified:
        responsible = await sync_to_async(Responsible.objects.filter)(telegram_id=user_id, is_active=True)
        responsible = await sync_to_async(responsible.first)()

        if responsible:
            # Если пользователь — ответственный, отправляем клавиатуру для работы с жалобами
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            list_complaints_button = KeyboardButton("Список жалоб")
            resolve_complaint_button = KeyboardButton("Закрыть жалобу")
            complain_button = KeyboardButton("Подать жалобу")
            keyboard.add(list_complaints_button, resolve_complaint_button, complain_button)

            # Проверка, является ли пользователь админом
            if user_id in admin_ids:
                add_responsible_button = KeyboardButton("Добавить ответственного")
                keyboard.add(add_responsible_button)
        else:
            # Если пользователь зарегистрирован, но не ответственный
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            complain_button = KeyboardButton("Подать жалобу")
            keyboard.add(complain_button)

        return keyboard
