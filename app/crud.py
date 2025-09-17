from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.util import await_only

from app import models, schemas
from app.auth import hash_password
from app.utils import generate_short_url

async def get_user_by_email(db: AsyncSession, email: str):
    """Находит пользователя по email"""
    query = select(models.User).where(models.User.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    """Создает нового пользователя"""
    hashed_password = hash_password(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user) # обновляем объект с новыми данными (чтобы id не был None)
    return db_user

async def create_short_url(db: AsyncSession, link: schemas.LinkCreate, user_id: int):
    """Создает новую короткую ссылку"""

    while True:
        short_url = generate_short_url()
        existing_link = await db.execute(select(models.Link).where(models.Link.short_url == short_url))
        if existing_link.scalar_one_or_none() is None:
            break

    db_link = models.Link(
        original_url=link.original_url,
        short_url=short_url,
        user_id=user_id
    )
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    return db_link

async def get_user_links(db: AsyncSession, user_id: int):
    """Возвращает все ссылки пользователя"""
    query = select(models.Link).where(models.Link.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()


async def delete_link(db: AsyncSession, link_id: int, user_id: int):
    if link_id:
        query = select(models.Link).where(models.Link.id == link_id).where(models.Link.user_id == user_id)
        result = await db.execute(query)
        link = result.scalar_one_or_none()
        if link:
            await db.delete(link)
            await db.commit()
            return link
    return None


async def get_link_by_original_url(db: AsyncSession, original_url: str):
    if original_url:
        query = select(models.Link).where(models.Link.original_url == original_url)
        result = await db.execute(query)
        link = result.scalar_one_or_none()
        return link
    return None