import logging
from aiogram.dispatcher.filters.state import StatesGroup, State
from asgiref.sync import sync_to_async
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from users.models import User
from ..db import get_user_from_db
from ..keyboard import get_user_keyboard
from ..utils import generate_safe_filename


class Registration(StatesGroup):
    full_name = State()
    room_number = State()
    pass_photo = State()


# Обработка команды /start
async def start_command(message: types.Message):
    keyboard = await get_user_keyboard(message.from_user.id)
    # Проверяем, зарегистрирован ли пользователь
    user = await sync_to_async(get_user_from_db)(message.from_user.id)

    if user:
        # Если пользователь зарегистрирован, выводим сообщение
        await message.answer("Вы уже зарегистрированы и не можете повторно запустить процесс регистрации.",
                             reply_markup=keyboard)
    else:
        # Если пользователь не зарегистрирован, начинаем процесс регистрации
        await message.answer(
            "Добро пожаловать!\nЗа использования бота не по назначению вы "
            "получается блокировку (Больше не сможете отправить жалобу на кого-то, попросить помощи в вопросах "
            "общежития и в будущем не сможете пользоваться комнатой отдыха. Спасибо за понимание.\n\nДля начала, "
            "пожалуйста, зарегистрируйтесь.", reply_markup=keyboard)


# Обработчик нажатия на кнопку "Регистрация"
async def register_command(message: types.Message):
    keyboard = await get_user_keyboard(message.from_user.id)
    # Проверяем, зарегистрирован ли пользователь
    user = await sync_to_async(get_user_from_db)(message.from_user.id)
    if user:
        await message.answer("Вы уже зарегистрированы и не можете повторно запустить процесс регистрации.",
                             reply_markup=keyboard)
    else:
        # Процесс регистрации пользователя
        await message.answer("Введите ваше ФИО полностью.")
        await Registration.full_name.set()


# Ввод ФИО
async def process_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Теперь введите номер вашей комнаты.")
    await Registration.room_number.set()


# Ввод номера комнаты
async def process_room_number(message: types.Message, state: FSMContext):
    await state.update_data(room_number=message.text)
    await message.answer("Теперь отправьте фото вашего пропуска.")
    await Registration.pass_photo.set()


# Обработка фото пропуска
async def process_pass_photo(message: types.Message, state: FSMContext):
    from ..main import bot
    data = await state.get_data()
    full_name = data.get('full_name')
    room_number = data.get('room_number')

    # Генерируем безопасное имя файла
    safe_filename = generate_safe_filename(full_name)

    # Получаем file_id и загружаем файл с серверов Telegram
    file_id = message.photo[-1].file_id
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    # Загружаем файл
    file = await bot.download_file(file_path)

    # Определяем путь для сохранения файла с именем ФИО
    local_file_path = f'media/pass_photos/{safe_filename}.jpg'

    # Сохраняем файл на сервере
    with open(local_file_path, 'wb') as f:
        f.write(file.read())

    # Сохраняем нового пользователя в базе данных
    user = await sync_to_async(User.objects.create)(
        full_name=full_name,
        room_number=room_number,
        pass_photo=local_file_path,  # Сохраняем путь к файлу
        telegram_id=message.from_user.id,  # Сохраняем telegram_id пользователя
        is_verified=False  # Пользователь еще не проверен
    )


    # keyboard = await get_user_keyboard(message.from_user.id)
    await message.answer("Спасибо! Ваши данные отправлены на проверку.")
    # await message.answer("Можете пользоваться ботом.", reply_markup=keyboard)
    logging.info("Пользователь отправил заявку.")
    await state.finish()


# Функция для регистрации хендлеров
def register_handlers_registration(dp: Dispatcher):
    dp.register_message_handler(start_command, commands="start")
    dp.register_message_handler(register_command, lambda message: message.text == "Регистрация")
    dp.register_message_handler(process_full_name, state=Registration.full_name)
    dp.register_message_handler(process_room_number, state=Registration.room_number)
    dp.register_message_handler(process_pass_photo, content_types=['photo'], state=Registration.pass_photo)
