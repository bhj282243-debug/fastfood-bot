import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import menu, orders, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting up...")
    yield
    print("Application shutting down...")

app = FastAPI(
    title="FastFood API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(menu.router, prefix="/api", tags=["Menu"])
app.include_router(orders.router, prefix="/api", tags=["Orders"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/setup")
async def setup_admin():
    """Создаёт/обновляет админа. Открыть один раз в браузере."""
    try:
        from passlib.context import CryptContext
        from sqlalchemy.future import select
        from database import AsyncSessionLocal
        from models import User

        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd.hash("admin123")

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter(User.username == "admin"))
            user = result.scalar_one_or_none()
            if user:
                user.hashed_password = hashed
                await session.commit()
                return {"status": "ok", "message": "Пароль обновлён", "login": "admin", "password": "admin123"}
            else:
                new_user = User(
                    username="admin",
                    email="admin@fastfood.uz",
                    hashed_password=hashed,
                    is_active=True
                )
                session.add(new_user)
                await session.commit()
                return {"status": "ok", "message": "Админ создан", "login": "admin", "password": "admin123"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="Not Found")
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Page not found")
