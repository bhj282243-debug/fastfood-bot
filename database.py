import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# URL вашей базы данных (замените данные на свои, если нужно)
# Пример для PostgreSQL: "postgresql+asyncpg://user:password@localhost:5432/fastfood"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/fastfood")

# Создаем асинхронный движок
# echo=False — чтобы не выводить лишние логи в консоль
# pool_pre_ping=True — чтобы соединение с БД автоматически восстанавливалось
engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    future=True, 
    pool_pre_ping=True
)

# Фабрика сессий
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Базовый класс для всех моделей
Base = declarative_base()

# Зависимость для получения сессии в других файлах (роутерах)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
