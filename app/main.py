from cgitb import reset

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from app import models, schemas, crud
from app.database import engine, get_db
from app.utils import generate_short_url

app = FastAPI(title="URL Shortener", version="0.1.0")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.run_sync(models.Base.metadata.create_all)

# Эндпоинт для проверки работы сервиса
@app.get("/")
async def root():
    return {"message": "URL Shortener is running!"}

# Запуск для разработки: uvicorn app.main:app --reload

# Эндпоинт для регистрации нового пользователя
# @app.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
# async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
#     """Создание нового пользователя"""
#     db_user = await crud.get_user_by_email(db=db, email=user.email)
#     if db_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Пользователь с таким email уже существует"
#         )
#
#     try:
#         new_user = await crud.create_user(db, user)
#         return new_user
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )

@app.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Создает нового пользователя в системе.
    """
    try:
        # Пытаемся создать пользователя. Если email не уникален, БД выбросит IntegrityError.
        new_user = await crud.create_user(db=db, user=user)
        return new_user

    except IntegrityError as e:
        # Ловим конкретное исключение о нарушении целостности данных (уникальности)
        await db.rollback()  # Важно: откатываем failed transaction
        # Проверяем, что ошибка именно про уникальность email
        if "unique" in str(e).lower() and "email" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
        else:
            # Если это какая-то другая ошибка целостности, поднимаем ее с общим сообщением
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Произошла ошибка при создании пользователя"
            )

# Эндпоинт для получения короткого URL
@app.post("/links", response_model=schemas.LinkOut)
async def create_short_url(
        link: schemas.LinkCreate,
        user_id: int,  #ВРЕМЕННО для теста. Передать user_id из токена
        db: AsyncSession = Depends(get_db)):
    """Создание короткого URL для авторизованного пользователя"""
    # Заменить на настоящую проверку токена
    new_link = await crud.create_short_url(db, link, user_id)
    return new_link

# Эндпоинт для редиректа по короткому URL
@app.get("/r/{short_url}")
async def redirect_to_original_url(short_url: str, db: AsyncSession = Depends(get_db)):
    """Редирект на полный URL по короткому"""
    query = select(models.Link).where(models.Link.short_url == short_url)
    result = await db.execute(query)
    link = result.scalar_one_or_none()

    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ссылка не найдена"
        )

    # Увеличение счетчика кликов
    link.clicks += 1
    await db.commit()

    # Перенаправление на оригинальный URL
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=link.original_url)
