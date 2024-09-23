from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from users.models import User
from bot.keyboard import get_user_keyboard


@receiver(post_save, sender=User)
def notify_user_verification(sender, instance, created, **kwargs):
    if not created and instance.is_verified:
        try:
            from bot.main import bot
            async_to_sync(bot.send_message)(
                instance.telegram_id,
                "Ваш аккаунт успешно подтверждён!"
            )
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
