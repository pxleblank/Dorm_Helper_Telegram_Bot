import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Dorm6HelperBot.settings')
django.setup()

import tracemalloc

tracemalloc.start()

import logging
from aiogram import types
from bot.handlers.registration import register_handlers_registration
from bot.handlers.complaints import register_handlers_complaints
from bot.handlers.admin import register_handlers_admin
from bot.keyboard import get_user_keyboard

from bot.bot_instance import dp

# Регистрация хендлеров
register_handlers_registration(dp)
register_handlers_complaints(dp)
register_handlers_admin(dp)


# Обработчик для любых сообщений без команд
@dp.message_handler()
async def handle_unknown_message(message: types.Message):
    keyboard = await get_user_keyboard(message.from_user.id)
    await message.answer("Такой команды нет.", reply_markup=keyboard)


async def on_startup(dp):
    # Приветственное сообщение в логах при запуске бота
    logging.info("Бот успешно запущен и готов к работе.")


# Основная функция
if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
