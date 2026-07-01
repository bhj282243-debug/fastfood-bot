import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
# Импортируем модули
from routers import menu, orders
import auth

# Управление запуском приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Здесь можно добавить логику проверки БД при старте
    print("Application starting up...")
    yield
    print("Application shutting down...")

# Инициализация FastAPI
app = FastAPI(
    title="FastFood API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Настройка CORS (разрешения для запросов)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение всех наших роутеров
app.include_router(menu.router, prefix="/api", tags=["Menu"])
app.include_router(orders.router, prefix="/api", tags=["Orders"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])

# Эндпоинт для проверки работы API
@app.get("/health")
async def health():
    return {"status": "ok"}

# Подключение папки со статическими файлами (html, css, js)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка для работы фронтенда (SPA)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Если путь начинается с api, но роутер не найден — отдаем 404
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="Not Found")
        
    # Иначе отдаем index.html для работы интерфейса
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # Если файла нет — ошибка
    raise HTTPException(status_code=404, detail="Page not found")
