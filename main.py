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

@app.get("/api/seed")
async def seed_menu():
    """Заполняет меню демо-данными с фото. Открыть один раз в браузере."""
    try:
        from sqlalchemy.future import select
        from sqlalchemy.orm import selectinload
        from database import AsyncSessionLocal
        from models import Category, Product

        MENU = [
            {
                "name": "Бургеры",
                "sort_order": 1,
                "products": [
                    {
                        "name": "Классический бургер",
                        "description": "Говяжья котлета, салат, томат, маринованный огурец, соус",
                        "price": 35000,
                        "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&q=80",
                        "is_popular": True,
                        "sort_order": 1,
                    },
                    {
                        "name": "Двойной чизбургер",
                        "description": "Две котлеты, двойной чеддер, лук, горчица, кетчуп",
                        "price": 48000,
                        "image_url": "https://images.unsplash.com/photo-1553979459-d2229ba7433b?w=400&q=80",
                        "is_popular": True,
                        "sort_order": 2,
                    },
                    {
                        "name": "Острый бургер",
                        "description": "Говяжья котлета, перец халапеньо, острый соус, сыр",
                        "price": 40000,
                        "image_url": "https://images.unsplash.com/photo-1594212699903-ec8a3eca50f5?w=400&q=80",
                        "is_popular": False,
                        "sort_order": 3,
                    },
                    {
                        "name": "Куриный бургер",
                        "description": "Хрустящее куриное филе, коул слоу, соус ранч",
                        "price": 38000,
                        "image_url": "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=400&q=80",
                        "is_popular": True,
                        "sort_order": 4,
                    },
                ],
            },
            {
                "name": "Картошка",
                "sort_order": 2,
                "products": [
                    {
                        "name": "Картофель фри",
                        "description": "Хрустящий картофель, крупная соль",
                        "price": 15000,
                        "image_url": "https://images.unsplash.com/photo-1630431341973-02e1b662ec35?w=400&q=80",
                        "is_popular": True,
                        "sort_order": 1,
                    },
                    {
                        "name": "Картофель по-деревенски",
                        "description": "Дольки с кожурой, специи, соус сметана",
                        "price": 18000,
                        "image_url": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400&q=80",
                        "is_popular": False,
                        "sort_order": 2,
                    },
                    {
                        "name": "Картофель с сыром",
                        "description": "Фри с плавленым чеддером и беконом",
                        "price": 22000,
                        "image_url": "https://images.unsplash.com/photo-1598679253544-2c97992403ea?w=400&q=80",
                        "is_popular": False,
                        "sort_order": 3,
                    },
                ],
            },
            {
                "name": "Снэки",
                "sort_order": 3,
                "products": [
                    {
                        "name": "Куриные наггетсы",
                        "description": "6 штук, хрустящая панировка, соус на выбор",
                        "price": 25000,
                        "image_url": "https://images.unsplash.com/photo-1562802378-063ec186a863?w=400&q=80",
                        "is_popular": True,
                        "sort_order": 1,
                    },
                    {
                        "name": "Куриные крылья",
                        "description": "8 штук, глазурь барбекю, соус ранч",
                        "price": 42000,
                        "image_url": "https://images.unsplash.com/photo-1527477396000-e27163b481c2?w=400&q=80",
                        "is_popular": False,
                        "sort_order": 2,
                    },
                    {
                        "name": "Луковые кольца",
                        "description": "Хрустящие, с соусом тартар",
                        "price": 18000,
                        "image_url": "https://images.unsplash.com/photo-1639744091981-2f9a94119e75?w=400&q=80",
                        "is_popular": False,
                        "sort_order": 3,
                    },
                    {
                        "name": "Хот-дог",
                        "description": "Говяжья сосиска, мягкая булка, горчица, кетчуп",
                        "price": 22000,
                        "image_url": "https://images.unsplash.com/photo-1612392062631-94440cf7e5bd?w=400&q=80",
                        "is_popular": False,
                        "sort_order": 4,
                    },
                ],
            },
            {
                "name": "Напитки",
                "sort_order": 4,
                "products": [
                    {
                        "name": "Кола",
                        "description": "500 мл, со льдом",
                        "price": 10000,
                        "image_url": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=400&q=80",
                        "is_popular": False,
                        "sort_order": 1,
                    },
                    {
                        "name": "Лимонад",
                        "description": "Домашний, лимон и мята, 400 мл",
                        "price": 14000,
                        "image_url": "https://images.unsplash.com/photo-1621263764928-df1444c5e859?w=400&q=80",
                        "is_popular": True,
                        "sort_order": 2,
                    },
                    {
                        "name": "Молочный коктейль",
                        "description": "Ваниль / шоколад / клубника, 400 мл",
                        "price": 20000,
                        "image_url": "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=400&q=80",
                        "is_popular": True,
                        "sort_order": 3,
                    },
                    {
                        "name": "Вода",
                        "description": "Негазированная, 500 мл",
                        "price": 6000,
                        "image_url": "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=400&q=80",
                        "is_popular": False,
                        "sort_order": 4,
                    },
                ],
            },
            {
                "name": "Десерты",
                "sort_order": 5,
                "products": [
                    {
                        "name": "Мороженое",
                        "description": "Ванильный рожок в шоколадной глазури",
                        "price": 12000,
                        "image_url": "https://images.unsplash.com/photo-1560008581-09826d1de69e?w=400&q=80",
                        "is_popular": False,
                        "sort_order": 1,
                    },
                    {
                        "name": "Шоколадный маффин",
                        "description": "Тёплый, с шоколадной начинкой",
                        "price": 16000,
                        "image_url": "https://images.unsplash.com/photo-1576618148400-f54bed99fcfd?w=400&q=80",
                        "is_popular": False,
                        "sort_order": 2,
                    },
                ],
            },
        ]

        async with AsyncSessionLocal() as session:
            # Проверяем — если меню уже есть, не дублируем
            existing = await session.execute(select(Category))
            if existing.scalars().first():
                return {
                    "status": "already_exists",
                    "message": "Меню уже заполнено. Управляй через /static/admin.html"
                }

            created_cats = 0
            created_prods = 0

            for cat_data in MENU:
                products = cat_data.pop("products")
                cat = Category(
                    name=cat_data["name"],
                    sort_order=cat_data["sort_order"],
                    is_active=True
                )
                session.add(cat)
                await session.flush()  # получаем cat.id

                for p in products:
                    prod = Product(
                        category_id=cat.id,
                        name=p["name"],
                        description=p["description"],
                        price=p["price"],
                        image_url=p["image_url"],
                        is_available=True,
                        is_popular=p["is_popular"],
                        sort_order=p["sort_order"],
                    )
                    session.add(prod)
                    created_prods += 1

                created_cats += 1

            await session.commit()

        return {
            "status": "ok",
            "message": f"Меню заполнено! Создано {created_cats} категорий и {created_prods} блюд.",
            "next": "Открой https://fastfood-bot-4bac.onrender.com чтобы увидеть результат"
        }

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
