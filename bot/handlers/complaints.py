from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import CallbackQuery
from asgiref.sync import sync_to_async
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
import logging

from bot.db import get_user_from_db
from bot.keyboard import get_user_keyboard, inline_keyboard_to_cancel_complaint, \
    inline_keyboard_to_take_complain_with_id, \
    inline_keyboard_to_join_group, inline_keyboard_to_cancel_complaint_progress
from complaints.models import Complaint, Responsible

# Включаем логирование
logging.basicConfig(level=logging.INFO)


class ComplaintForm(StatesGroup):
    waiting_for_complaint_text = State()  # Состояние для ввода текста жалобы
    waiting_for_complaint_id = State()  # Состояние для ввода ID жалобы для решения
    waiting_for_complaint_id_take = State()  # Состояние для ввода ID жалобы для взятия


# Обработка команды "Подать жалобу" - начало подачи жалобы
async def create_complaint(message: types.Message):
    keyboard = await get_user_keyboard(message.from_user.id)

    user = await sync_to_async(get_user_from_db)(message.from_user.id)  # Получаем пользователя по telegram_id

    if user is None:
        await message.answer("Вы не зарегистрированы.", reply_markup=keyboard)
    elif user.is_blocked:
        await message.answer("Вы заблокированы.")
    else:
        if user.is_verified:
            # Проверяем, не отправлял ли уже пользователь жалобу, которая не была обработана
            if await sync_to_async(Complaint.objects.filter(user=user, is_resolved=False).exists)():
                await message.answer("Вы уже отправили жалобу, дождитесь её решения.", reply_markup=keyboard)
            else:
                cancel_complaint_in_text_keyboard = await inline_keyboard_to_cancel_complaint_progress()
                await message.answer("Пожалуйста, напишите текст вашей жалобы.",
                                     reply_markup=cancel_complaint_in_text_keyboard)
                await ComplaintForm.waiting_for_complaint_text.set()  # Устанавливаем состояние
        else:
            await message.answer("Ваш аккаунт ещё не подтверждён.")


# Обработка текста жалобы
async def process_complaint_text(message: types.Message, state: FSMContext):
    from ..main import bot
    keyboard = await get_user_keyboard(message.from_user.id)
    user = await sync_to_async(get_user_from_db)(message.from_user.id)
    if user and user.is_verified and not user.is_blocked:
        complaint_text = message.text

        # Сохраняем жалобу в базе данных (синхронная операция обёрнута в sync_to_async)
        complaint = await sync_to_async(Complaint.objects.create)(user=user, description=complaint_text)

        # Получаем ID созданной жалобы
        complaint_id = complaint.id

        complaint_keyboard = await inline_keyboard_to_cancel_complaint(complaint_id)
        await message.answer("Ваша жалоба принята и будет рассмотрена в ближайшее время.", reply_markup=keyboard)
        await message.answer("Чтобы отменить жалобу нажмите на кнопку:", reply_markup=complaint_keyboard)

        # Уведомляем всех активных ответственных
        responsibles = await sync_to_async(list)(Responsible.objects.filter(is_active=True))
        for responsible in responsibles:
            try:
                username_ = await bot.get_chat(user.telegram_id)
                username_ = username_.username
                await bot.send_message(
                    responsible.telegram_id,
                    f"Новая жалоба от {user.full_name} (Комната {user.room_number}) (@{username_}):\n\nID: {complaint_id}\n\n{complaint_text}",
                    reply_markup=keyboard
                )
                take_complain_with_id_keyboard = await inline_keyboard_to_take_complain_with_id(complaint_id)
                await bot.send_message(
                    responsible.telegram_id,
                    f"Нажмите, чтобы взять жалобу.",
                    reply_markup=take_complain_with_id_keyboard
                )
            except Exception as e:
                logging.error(f"Ошибка при отправке уведомления ответственному: {e}")

        # Завершаем FSM
        await state.finish()
    else:
        await message.answer("Что-то пошло не так. Проверьте, активен ли ваш аккаунт.", reply_markup=keyboard)
        await state.finish()


# Обработка команды "Взять жалобу в работу"
async def take_complaint(call: CallbackQuery):
    from ..main import bot
    keyboard = await get_user_keyboard(call.from_user.id)

    responsible = await sync_to_async(Responsible.objects.filter)(telegram_id=call.from_user.id, is_active=True)
    responsible = await sync_to_async(responsible.first)()

    if not responsible:
        await call.message.answer("Вы не являетесь ответственным или ваш доступ отключен.", reply_markup=keyboard)
        return

    complaint_id = int(call.data.split(":")[1])

    try:
        @sync_to_async
        def take_complaint_transaction():
            complaint = Complaint.objects.select_for_update().get(id=complaint_id)
            if complaint.status != 'pending':
                return complaint, complaint  # Жалоба уже в процессе или решена
            complaint.status = 'in_progress'
            complaint.responsible_in_progress = responsible
            complaint.save()
            return complaint, None

        # Получаем жалобу и проверяем статус
        complaint, error = await take_complaint_transaction()

        if error:
            if complaint.status == 'pending':
                responsible_in_progress = await sync_to_async(lambda: complaint.responsible_in_progress.full_name)()

                await call.message.answer(
                    f"Жалоба ID {complaint_id} уже взята в работу ответственным: {responsible_in_progress}.",
                    reply_markup=keyboard)
            else:
                await call.message.answer(f"Жалоба с ID {complaint_id} не найдена или уже взята в работу.",
                                          reply_markup=keyboard)
        else:
            await call.message.answer(f"Вы взяли жалобу ID {complaint_id} в работу.", reply_markup=keyboard)

            # Уведомление остальных ответственных о том, что жалоба взята в работу
            responsibles = await sync_to_async(list)(Responsible.objects.filter(is_active=True))
            responsibles = [r for r in responsibles if r.telegram_id != responsible.telegram_id]
            for other_responsible in responsibles:
                try:
                    join_keyboard = await inline_keyboard_to_join_group(complaint_id)
                    await bot.send_message(other_responsible.telegram_id,
                                           f"Жалоба ID {complaint_id} была взята в работу ответственным {responsible.full_name}.",
                                           reply_markup=join_keyboard)
                except Exception as e:
                    logging.error(f"Ошибка при отправке уведомления ответственному: {e}")

    except (ValueError, Complaint.DoesNotExist):
        await call.message.answer("Жалоба с таким ID не найдена или уже решена.", reply_markup=keyboard)

    except Responsible.DoesNotExist:
        await call.message.answer("Ответственный с таким ID не найден.")


# Обработчик присоединения к жалобе
async def join_complaint(call: CallbackQuery):
    from ..main import bot
    complaint_id = int(call.data.split(":")[1])

    responsible = await sync_to_async(Responsible.objects.filter)(telegram_id=call.from_user.id, is_active=True)
    responsible = await sync_to_async(responsible.first)()

    if not responsible:
        await call.message.answer("Вы не являетесь ответственным или ваш доступ отключен.")
        return

    try:
        # Проверяем, не находится ли ответственный уже в группе
        @sync_to_async
        def check_responsible_in_complaint():
            complaint = Complaint.objects.get(id=complaint_id)
            return responsible in complaint.responsibles.all(), complaint

        already_in_group, complaint = await check_responsible_in_complaint()

        if already_in_group:
            await call.message.answer("Вы уже присоединились к этой жалобе.")
        else:
            # Обновляем жалобу, добавляем ещё одного ответственного
            @sync_to_async
            def add_responsible_to_complaint():
                complaint.responsibles.add(responsible)
                complaint.save()
                return complaint

            complaint = await add_responsible_to_complaint()

        # Уведомляем всех ответственных о новом участнике
        responsibles = await sync_to_async(list)(Responsible.objects.filter(is_active=True))
        for other_responsible in responsibles:
            try:
                join_keyboard = await inline_keyboard_to_join_group(complaint_id)
                await bot.send_message(
                    other_responsible.telegram_id,
                    f"Жалоба ID {complaint_id} теперь обрабатывается группой из {complaint.responsibles.count()} человек.",
                    reply_markup=join_keyboard
                )
            except Exception as e:
                logging.error(f"Ошибка при отправке уведомления ответственному: {e}")

        await call.message.answer(f"Вы присоединились к обработке жалобы ID {complaint_id}.")

    except Complaint.DoesNotExist:
        await call.message.answer("Жалоба с таким ID не найдена.")


# Обработка команды "Закрыть жалобу" ответственным
async def resolve_complaint(message: types.Message):
    keyboard = await get_user_keyboard(message.from_user.id)

    responsible = await sync_to_async(Responsible.objects.filter)(telegram_id=message.from_user.id, is_active=True)
    responsible = await sync_to_async(responsible.first)()

    if not responsible:
        await message.answer("Вы не являетесь ответственным или ваш доступ отключен.", reply_markup=keyboard)
        return

    # Запрашиваем номер жалобы (или ID жалобы)
    await message.answer("Введите ID жалобы, которую вы хотите закрыть:")

    # FSM для получения ID жалобы
    await ComplaintForm.waiting_for_complaint_id.set()


async def process_complaint_id(message: types.Message, state: FSMContext):
    from ..main import bot
    keyboard = await get_user_keyboard(message.from_user.id)
    try:
        complaint_id = int(message.text)

        # Используем синхронную транзакцию для избежания гонки условий
        @sync_to_async
        def close_complaint_transaction():
            try:
                complaint = Complaint.objects.select_for_update().get(id=complaint_id)
                if complaint.is_resolved:
                    return None, complaint  # Жалоба уже решена
                complaint.is_resolved = True
                complaint.status = 'resolved'
                complaint.save()
                return complaint, None
            except Complaint.DoesNotExist:
                return None, None  # Жалоба не найдена

        # Получаем жалобу и проверяем статус
        complaint, error = await close_complaint_transaction()

        if not complaint:
            await message.answer("Жалоба с таким ID не найдена или уже решена.", reply_markup=keyboard)
        else:
            await message.answer(f"Жалоба ID {complaint_id} успешно решена.", reply_markup=keyboard)

            # Уведомляем студента о решении его жалобы
            try:
                responsible = await sync_to_async(Responsible.objects.filter)(telegram_id=message.from_user.id,
                                                                              is_active=True)
                responsible = await sync_to_async(responsible.first)()
                user_telegram_id = await sync_to_async(lambda: complaint.user.telegram_id)()
                responsible_full_name = responsible.full_name

                await bot.send_message(
                    user_telegram_id,
                    f"Ваша жалоба решена ответственным: {responsible_full_name}.", reply_markup=keyboard
                )
            except Exception as e:
                logging.error(f"Ошибка при отправке уведомления студенту: {e}")

    except (ValueError, Complaint.DoesNotExist):
        await message.answer("Неверный формат ID или жалоба с таким ID не найдена.", reply_markup=keyboard)

    await state.finish()


# Обработка команды для получения списка жалоб
async def list_complaints(message: types.Message):
    keyboard = await get_user_keyboard(message.from_user.id)

    responsible = await sync_to_async(Responsible.objects.filter)(telegram_id=message.from_user.id, is_active=True)
    responsible = await sync_to_async(responsible.first)()

    if not responsible:
        await message.answer("Вы не являетесь ответственным или ваш доступ отключен.", reply_markup=keyboard)
        return

    # Получаем все открытые жалобы
    complaints = await sync_to_async(list)(Complaint.objects.filter(is_resolved=False))

    if not complaints:
        await message.answer("Нет открытых жалоб.", reply_markup=keyboard)
        return

    # Формируем список жалоб с учётом их статуса
    complaint_list = []
    for complaint in complaints:
        if complaint.status == 'in_progress':
            responsible_in_progress = await sync_to_async(lambda: complaint.responsible_in_progress.full_name)()
            complaint_list.append(
                f"ID: {complaint.id} - {complaint.description} (В процессе ответственным: {responsible_in_progress})")
        else:
            complaint_list.append(f"ID: {complaint.id} - {complaint.description} (Ожидает решения)")

    temp = '\n'.join(complaint_list)

    await message.answer(f"Открытые жалобы:\n{temp}", reply_markup=keyboard)


async def cancel_complaint(call: CallbackQuery):
    from ..main import bot
    data = call.data.split(":")
    complaint_id = int(data[1])

    try:
        # Находим жалобу и проверяем её статус с использованием sync_to_async
        complaint = await sync_to_async(Complaint.objects.get)(id=complaint_id)

        if complaint.is_resolved is True:
            await call.message.answer("Эта жалоба уже закрыта.")
            return

        # Закрываем жалобу
        complaint.status = 'resolved'
        complaint.is_resolved = True
        await sync_to_async(complaint.save)()

        await call.message.answer(f"Вы успешно отменили жалобу ID {complaint_id}. Жалоба закрыта.")

        # Уведомляем ответственных о том, что жалоба была отменена
        responsibles = await sync_to_async(list)(Responsible.objects.filter(is_active=True))
        for responsible in responsibles:
            try:
                await bot.send_message(
                    responsible.telegram_id,
                    f"Жалоба ID {complaint_id} была отменена пользователем {call.from_user.full_name}."
                )
            except Exception as e:
                logging.error(f"Ошибка при отправке уведомления ответственному: {e}")

    except Complaint.DoesNotExist:
        await call.message.answer("Жалоба с таким ID не найдена.")


# Обработка нажатия на кнопку "Отмена" в момент подачи жалобы
async def cancel_complaint_process(call: CallbackQuery, state: FSMContext):
    keyboard = await get_user_keyboard(call.from_user.id)

    # Завершаем процесс подачи жалобы
    await state.finish()
    await call.message.edit_reply_markup()  # Убираем клавиатуру после отмены
    await call.message.answer("Подача жалобы отменена.", reply_markup=keyboard)


# Функция для регистрации хендлеров
def register_handlers_complaints(dp: Dispatcher):
    dp.register_message_handler(create_complaint, lambda message: message.text == "Подать жалобу")
    dp.register_message_handler(process_complaint_text, state=ComplaintForm.waiting_for_complaint_text)
    dp.register_callback_query_handler(take_complaint, lambda call: call.data.startswith("take_complain:"))
    dp.register_callback_query_handler(join_complaint, lambda call: call.data.startswith("join_complaint:"))
    dp.register_message_handler(resolve_complaint, lambda message: message.text == "Закрыть жалобу")
    dp.register_message_handler(process_complaint_id, state=ComplaintForm.waiting_for_complaint_id)
    dp.register_message_handler(list_complaints, lambda message: message.text == "Список жалоб")
    dp.register_callback_query_handler(cancel_complaint, lambda call: call.data.startswith("cancel_complaint:"))
    dp.register_callback_query_handler(cancel_complaint_process, lambda call: call.data == "cancel_complaint_process", state="*")
