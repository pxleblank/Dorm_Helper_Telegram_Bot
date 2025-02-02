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
        await message.answer(
            "Вас приветствует студенческий совет общежития номер 6!\nС помощью этого бота вы можете связаться со "
            "студсоветом по вопросам, касающимся каких-либо проблемных ситуаций с соседями по блоку, этажу и т.д., "
            "а также получить поддержку, если вы или ваш сосед нуждаетесь в этом. Вы можете свободно делиться "
            "ситуацией и рассчитывать на помощь!\n\n"
            "Если вы или ваш сосед нуждаетесь в помощи, не стесняйтесь и не бойтесь обращаться к психологам психологического центра НГУ "
            "или допсихологам(это сообщество подготовленных студентов-волонтеров  оказывающих консультативную и базовую психоэмоциональную "
            "поддержку жизненных ситуациях). Это бесплатно и безопасно. Для этого вы можете перейти по следующим ссылкам:\n"
            "1.Ссылка на группу отдела психологической поддержки НГУ ВКонтакте: https://vk.com/oppo_nsu\n"
            "2.Форма для записи на допсихологическую консультацию: https://vk.cc/crju6g\n"
            "3.Форма для записи на личную консультацию у психолога: https://forms.gle/Mc6AdpPzSr69xAVc\n\n"
            "Обращаем ваше внимание на то, что за использование бота не по назначению вы получаете блокировку"
            "(больше не сможете: отправить обращение, попросить помощи в вопросах по общежитию и, в будущем, пользоваться комнатой отдыха).\n"
            "Благодарим за понимание!\n\n"
            "Не стесняйтесь обращаться за помощью – мы всегда рады помочь вам!\n\n"
            "Вы уже зарегистрированы!", reply_markup=keyboard)
    else:
        # Если пользователь не зарегистрирован, начинаем процесс регистрации
        await message.answer(
            "Вас приветствует студенческий совет общежития номер 6!\nС помощью этого бота вы можете связаться со "
            "студсоветом по вопросам, касающимся каких-либо проблемных ситуаций с соседями по блоку, этажу и т.д., "
            "а также получить поддержку, если вы или ваш сосед нуждаетесь в этом. Вы можете свободно делиться "
            "ситуацией и рассчитывать на помощь!\n\n"
            "Если вы или ваш сосед нуждаетесь в помощи, не стесняйтесь и не бойтесь обращаться к психологам психологического центра НГУ "
            "или допсихологам(это сообщество подготовленных студентов-волонтеров  оказывающих консультативную и базовую психоэмоциональную "
            "поддержку жизненных ситуациях). Это бесплатно и безопасно. Для этого вы можете перейти по следующим ссылкам:\n"
            "1.Ссылка на группу отдела психологической поддержки НГУ ВКонтакте: https://vk.com/oppo_nsu\n"
            "2.Форма для записи на допсихологическую консультацию: https://vk.cc/crju6g\n"
            "3.Форма для записи на личную консультацию у психолога: https://forms.gle/Mc6AdpPzSr69xAVc\n\n"
            "Обращаем ваше внимание на то, что за использование бота не по назначению вы получаете блокировку"
            "(больше не сможете: отправить обращение, попросить помощи в вопросах по общежитию и, в будущем, пользоваться комнатой отдыха).\n"
            "Благодарим за понимание!\n\n"
            "Не стесняйтесь обращаться за помощью – мы всегда рады помочь вам!\n\n"
            "Для начала, пожалуйста, зарегистрируйтесь.", reply_markup=keyboard)


# Обработчик нажатия на кнопку "Регистрация"
async def register_command(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:  # Пользователь уже в процессе регистрации
        step_name = current_state.split(":")[-1]  # Получаем текущий шаг регистрации
        instructions = {
            "full_name": "Введите ваше ФИО полностью.",
            "room_number": "Введите номер вашей комнаты.",
            "pass_photo": "Отправьте фото вашего пропуска.",
        }
        await message.answer(
            f"Вы уже начали процесс регистрации. {instructions.get(step_name, 'Пожалуйста, завершите регистрацию.')}"
        )
        return

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
    from ..bot_instance import bot
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
    local_file_path = f'/app/media/pass_photos/{safe_filename}.jpg'

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
    dp.register_message_handler(register_command, lambda message: message.text == "Регистрация", state="*")
    dp.register_message_handler(process_full_name, state=Registration.full_name)
    dp.register_message_handler(process_room_number, state=Registration.room_number)
    dp.register_message_handler(process_pass_photo, content_types=['photo'], state=Registration.pass_photo)
