import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Dorm6HelperBot.settings')
django.setup()

import tracemalloc

tracemalloc.start()

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode

from config import API_TOKEN
from bot.handlers.registration import register_handlers_registration
from bot.handlers.complaints import register_handlers_complaints
from bot.keyboard import get_user_keyboard

# Инициализируем бота и диспетчер
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())

# Регистрация хендлеров
register_handlers_registration(dp)
register_handlers_complaints(dp)


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
