import re
from unidecode import unidecode


def generate_safe_filename(full_name):
    # Транслитерируем имя, если необходимо (например, из кириллицы в латиницу)
    full_name = unidecode(full_name)

    # Убираем всё кроме букв, цифр и пробелов
    safe_name = re.sub(r'[^a-zA-Z0-9 ]', '', full_name)

    # Заменяем пробелы на подчеркивания
    safe_name = safe_name.replace(' ', '_')

    return safe_name