from passlib.context import CryptContext

# Настройка хеширования паролей алгоритмом bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Преобразует plaintext пароль в хеш"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие хеша и пароля"""
    return pwd_context.verify(plain_password, hashed_password)
