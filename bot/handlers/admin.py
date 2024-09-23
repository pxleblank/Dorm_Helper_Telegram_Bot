from aiogram.dispatcher.filters.state import StatesGroup, State
from asgiref.sync import sync_to_async
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from bot.config import admin_ids
from complaints.models import Responsible


class AddResponsible(StatesGroup):
    waiting_for_id = State()
    waiting_for_full_name = State()


# Команда для начала процесса добавления ответственного
async def start_add_responsible(message: types.Message):
    if message.from_user.id not in admin_ids:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    await message.answer("Введите ID пользователя, которого хотите назначить ответственным.")
    await AddResponsible.waiting_for_id.set()


async def process_id(message: types.Message, state: FSMContext):
    user_id = message.text.strip()

    # Проверяем, что ID является числом
    if not user_id.isdigit():
        await message.answer("ID должен быть числом. Пожалуйста, введите правильный ID.")
        return

    # Сохраняем ID в состояние FSM
    await state.update_data(user_id=int(user_id))
    await message.answer("Теперь введите имя пользователя.")
    await AddResponsible.waiting_for_full_name.set()


async def process_full_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()

    # Получаем ID пользователя из состояния FSM
    user_data = await state.get_data()
    user_id = user_data['user_id']

    # Сохраняем ответственного в базе данных
    responsible, created = await sync_to_async(Responsible.objects.get_or_create)(
        telegram_id=user_id,
        defaults={'full_name': full_name}
    )

    if created:
        await message.answer(f"Пользователь {full_name} (ID: {user_id}) добавлен как ответственный.")
    else:
        await message.answer(f"Пользователь {full_name} (ID: {user_id}) уже зарегистрирован как ответственный.")

    # Завершаем FSM
    await state.finish()


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(start_add_responsible, lambda message: message.text == "Добавить ответственного")
    dp.register_message_handler(process_id, state=AddResponsible.waiting_for_id)
    dp.register_message_handler(process_full_name, state=AddResponsible.waiting_for_full_name)
