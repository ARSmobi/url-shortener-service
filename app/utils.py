import secrets
import string


def generate_short_url(length: int = 6) -> str:
    """Генерирует короткий URL"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))
