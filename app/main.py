from cgitb import reset

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from starlette.requests import Request

from app import models, schemas, crud
from app.database import engine, get_db
from app.utils import generate_short_url
from app.auth import verify_token, create_access_token, verify_password

app = FastAPI(title="URL Shortener", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Разрешить запросы с этих доменов (Заменить на реальный домен)
    allow_credentials=True,  # Разрешить куки
    allow_methods=["*"],  # Разрешить все методы
    allow_headers=["*"],  # Разрешить все заголовки
)

# Раздача файлы из папки app/static
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# @app.on_event("startup")
# async def startup():
#     async with engine.begin() as conn:
#         # await conn.run_sync(models.Base.metadata.drop_all)
#         await conn.run_sync(models.Base.metadata.create_all)

# Эндпоинт для проверки работы сервиса
# @app.get("/")
# async def root():
#     return {"message": "URL Shortener is running!"}

# Запуск для разработки: uvicorn app.main:app --reload

# Эндпоинт для регистрации нового пользователя
@app.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """Создание нового пользователя"""
    db_user = await crud.get_user_by_email(db=db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )

    try:
        new_user = await crud.create_user(db, user)
        return new_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Схема аутентификации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)):
    """Проверка токена и возврат текущего пользователя"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверный токен",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Проверка токена
    payload = verify_token(token)
    if not payload:
        raise credentials_exception

    # Извлекаем user_id из токена
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    # Получение пользователя из БД
    user = await db.get(models.User, int(user_id))
    if not user:
        raise credentials_exception

    return user

# Эндпоинт для получения короткого URL
@app.post("/links", response_model=schemas.LinkOut)
async def create_short_url(
        link: schemas.LinkCreate,
        current_user: models.User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    """Создание короткого URL для авторизованного пользователя"""
    if await crud.get_link_by_original_url(db=db, original_url=link.original_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ссылка с таким URL уже существует"
        )
    new_link = await crud.create_short_url(db=db, link=link, user_id=current_user.id)
    return new_link

# Эндпоинт для получения списка ссылок пользователя
@app.get("/links", response_model=list[schemas.LinkOut])
async def get_user_links(
        current_user: models.User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    """Получение списка ссылок пользователя"""
    return await crud.get_user_links(db=db, user_id=current_user.id)

# Эндпоинт для удаления ссылки
@app.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
        link_id: int,
        current_user: models.User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    """Удаление ссылки пользователя"""
    if await crud.delete_link(db=db, link_id=link_id, user_id=current_user.id):
        return {
            "message": "Ссылка удалена",
            "link_id": link_id
        }
    if not await crud.get_link_by_id(db=db, link_id=link_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ссылка не найдена"
        )

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

# Эндпоинт для получения информации о пользователе и аутентификации
@app.post("/token")
async def login_for_access_token(
        from_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)):
    """Аутентификация пользователя и получение токена"""
    user = await crud.get_user_by_email(db=db, email=from_data.username)
    if not user or not verify_password(from_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Получение токена с данными пользователя
    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("app/static/index.html", "r") as f:
        return f.read()

@app.exception_handler(500)
async def internal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"},
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"detail": "Не найдено"},
    )
