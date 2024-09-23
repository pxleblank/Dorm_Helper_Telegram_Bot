from users.models import User


def get_user_from_db(telegram_id):
    try:
        user = User.objects.get(telegram_id=telegram_id)
        return user
    except User.DoesNotExist:
        return None
