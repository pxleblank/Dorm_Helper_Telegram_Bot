from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from users.models import User
from bot.keyboard import get_user_keyboard
from bot.bot_instance import bot


@receiver(post_save, sender=User)
def notify_user_verification(sender, instance, created, **kwargs):
    if not created and instance.is_verified:
        try:
            keyboard = async_to_sync(get_user_keyboard)(instance.telegram_id)
            async_to_sync(bot.send_message)(
                instance.telegram_id,
                "Ваш аккаунт успешно подтверждён!",
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
