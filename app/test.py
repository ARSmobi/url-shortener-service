try:
    import fastapi
    print("FastAPI успешно импортирован!")
    print(f"Версия FastAPI: {fastapi.__version__}")
except ImportError as e:
    print(f"Ошибка импорта: {e}")
