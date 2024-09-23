# # Несколько попыток отправить сообщение
# async def send_message_with_retry(user_id, text, retries=5, delay=2):
#     for i in range(retries):
#         try:
#             await bot.send_message(user_id, text)
#             break  # Сообщение успешно отправлено, выходим из цикла
#         except asyncio.exceptions.TimeoutError as e:
#             if i < retries - 1:  # Если есть еще попытки
#                 await asyncio.sleep(delay)  # Ждем перед повторной попыткой
#             else:
#                 logging.error(f"Не удалось отправить сообщение пользователю {user_id}. Ошибка: {e}")
#
# Пример: await send_message_with_retry(responsible.telegram_id, f"Новая жалоба от {user.full_name} (Комната {user.room_number}):\n\n{complaint_text}")
# Ещё пример:
# for responsible in responsibles:
#     try:
#         await bot.send_message(responsible.telegram_id, f"Новая жалоба от {user.full_name} (Комната {user.room_number}):\n\n{complaint_text}")
#         await asyncio.sleep(0.5)  # Задержка между отправками
#     except Exception as e:
#         logging.error(f"Ошибка при отправке уведомления ответственному: {e}")



# # Список команд
# @dp.message_handler(commands=['help'])
# async def help_command(message: types.Message):
#     # Получаем пользователя из базы данных
#     user = await sync_to_async(get_user_from_db)(message.from_user.id)
#
#     if not user:
#         # Если пользователь не зарегистрирован, показываем только базовые команды
#         await message.answer("Вы не зарегистрированы. Доступные команды:\n/start - Регистрация\n/help - Список команд")
#     else:
#         # Основные команды для всех пользователей
#         commands = [
#             "/help - Список команд",
#         ]
#
#         # Если пользователь проверен, добавляем дополнительные команды
#         if user.is_verified:
#             commands.append("/complain - Подать жалобу")
#
#         # Если пользователь является ответственным, добавляем команды для ответственных
#         responsible = await sync_to_async(Responsible.objects.filter)(telegram_id=message.from_user.id,
#                                                                       is_active=True)
#         responsible = await sync_to_async(responsible.first)()
#
#         if responsible:
#             commands.extend([
#                 "/list_complaints - Просмотр открытых жалоб",
#                 "/resolve_complaint - Решить жалобу"
#             ])
#
#         # Формируем и отправляем список доступных команд
#         command_list = "\n".join(commands)
#         await message.answer(f"Доступные команды:\n{command_list}")