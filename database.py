import os
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/fastfood")

# Убираем query string из URL если есть
if "?" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

# Корректный SSL для Neon — верификация сертификата включена
ssl_context = ssl.create_default_context()
# check_hostname=True и CERT_REQUIRED — значения по умолчанию, не отключаем

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args={"ssl": ssl_context}
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
