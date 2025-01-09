import os
import requests
from aiogram import Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from ..config import UNV_USERS_API_URL, admin_ids
from Dorm6HelperBot import settings
from bot.bot_instance import bot, dp


# Хранилище текущего индекса пользователей
current_user_index = {}
total_users = {}


# Обработка кнопки "Неверифицированные пользователи"
async def show_unverified_users(message: types.Message):
    if message.from_user.id not in admin_ids:
        await message.reply("У вас нет прав для использования этой команды.")
        return
    response = requests.get(UNV_USERS_API_URL)
    if response.status_code == 200:
        users = response.json()
        if users:
            current_user_index[message.chat.id] = 0
            total_users[message.chat.id] = len(users)  # Сохраняем общее количество пользователей
            await send_user_info(message.chat.id, users, 0)
        else:
            await message.answer("Нет неверифицированных пользователей.")
    else:
        await message.answer("Ошибка при получении данных о пользователях.")


# Отправка данных пользователя с кнопками
async def send_user_info(chat_id, users, index):
    user = users[index]
    keyboard = InlineKeyboardMarkup(row_width=2)
    if index > 0:
        keyboard.add(InlineKeyboardButton("⬅️ Предыдущий", callback_data=f"prev_{index}"))

    if index < len(users) - 1:
        keyboard.add(InlineKeyboardButton("➡️ Следующий", callback_data=f"next_{index}"))
    keyboard.add(
        InlineKeyboardButton("✅ Верифицировать", callback_data=f"verify_{user['id']}"),
        InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{user['id']}")
    )
    keyboard.row(InlineKeyboardButton("Закрыть", callback_data="close"))

    # Полный путь к файлу
    photo_path = os.path.join(settings.MEDIA_ROOT, user['pass_photo'])

    # Открываем файл и отправляем его
    with open(photo_path, 'rb') as photo:
        await bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=(
                f"Пользователь {index + 1} из {total_users[chat_id]}:\n"
                f"Имя: {user['full_name']}\n"
                f"Комната: {user['room_number']}"
            ),
            reply_markup=keyboard
        )


# Обработка inline-кнопок для переключения
async def process_navigation(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id
    response = requests.get(UNV_USERS_API_URL)

    if response.status_code == 200:
        users = response.json()
        current_index = int(callback_query.data.split('_')[1])

        # Определяем новый индекс
        if "next" in callback_query.data:
            current_index += 1
        elif "prev" in callback_query.data:
            current_index -= 1

        # Проверяем корректность индекса
        if 0 <= current_index < len(users):
            current_user_index[chat_id] = current_index

            # Удаляем предыдущее сообщение
            await bot.delete_message(chat_id=chat_id, message_id=message_id)

            # Отправляем новое сообщение
            await send_user_info(chat_id, users, current_index)
        else:
            await bot.answer_callback_query(callback_query.id, "Невозможно переключиться.")
    else:
        await callback_query.answer("Ошибка при загрузке пользователей.")


# Обработка кнопки верификации
async def verify_user(callback_query: types.CallbackQuery):
    user_id = callback_query.data.split('_')[1]

    # Отправляем запрос на верификацию пользователя
    requests.post(f"http://dorm6.nsu.ru/users/verify_user/{user_id}/")

    # Удаляем текущее сообщение
    await callback_query.message.delete()

    await callback_query.message.answer("Пользователь верифицирован.")

    # Получаем список пользователей
    response = requests.get(UNV_USERS_API_URL)
    if response.status_code == 200:
        users = response.json()
        chat_id = callback_query.message.chat.id

        # Обновляем общее количество пользователей
        total_users[chat_id] = len(users)

        # Получаем текущий индекс пользователя
        current_index = current_user_index.get(chat_id, 0)

        # Проверяем, если индекс не последний, то переключаем на следующего
        if current_index + 1 < len(users):
            current_index += 1
        else:
            # Если это последний, то возвращаем на первый
            current_index = 0

        # Обновляем индекс
        current_user_index[chat_id] = current_index

        # Отправляем информацию о следующем пользователе
        await send_user_info(chat_id, users, current_index)
    else:
        await callback_query.message.answer("Ошибка при загрузке пользователей.")


# Обработка кнопки удаления
async def delete_user(callback_query: types.CallbackQuery):
    user_id = callback_query.data.split('_')[1]
    requests.post(f"http://dorm6.nsu.ru/users/delete_user/{user_id}/")
    await callback_query.message.edit_caption("Пользователь удалён.")


# Обработка кнопки закрытия
async def close_menu(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await callback_query.answer("Меню закрыто.")


def register_handlers_unverified_users(dp: Dispatcher):
    dp.register_message_handler(show_unverified_users, lambda message: message.text == "Неверифицированные пользователи")
    dp.register_callback_query_handler(process_navigation, lambda c: c.data.startswith(('next_', 'prev_')))
    dp.register_callback_query_handler(verify_user, lambda c: c.data.startswith('verify_'))
    dp.register_callback_query_handler(delete_user, lambda c: c.data.startswith('delete_'))
    dp.register_callback_query_handler(close_menu, lambda c: c.data == "close")
