from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from database import get_db
from models import Product, Category, ProductOption, User
from auth import get_current_admin
import schemas

router = APIRouter()

# ──────────────────────────────────────────────
#  ПУБЛИЧНЫЕ эндпоинты (без авторизации)
#  Клиент читает меню — это нормально
# ──────────────────────────────────────────────

@router.get("/categories", response_model=List[schemas.Category])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Category)
        .filter(Category.is_active == True)
        .order_by(Category.sort_order)
    )
    return result.scalars().all()

@router.get("/menu", response_model=List[schemas.Category])
async def get_menu(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Category)
        .filter(Category.is_active == True)
        .options(selectinload(Category.products).selectinload(Product.options))
        .order_by(Category.sort_order)
    )
    return result.scalars().all()

@router.get("/products", response_model=List[schemas.Product])
async def get_products(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Product)
        .options(selectinload(Product.options))
        .filter(Product.is_available == True)
        .order_by(Product.sort_order)
    )
    if category_id:
        stmt = stmt.filter(Product.category_id == category_id)
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.filter(or_(Product.name.ilike(search_filter), Product.description.ilike(search_filter)))
    result = await db.execute(stmt)
    return result.scalars().all()

# ВАЖНО: /products/popular должен быть ДО /products/{product_id}
@router.get("/products/popular", response_model=List[schemas.Product])
async def get_popular_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product)
        .filter(Product.is_popular == True, Product.is_available == True)
        .options(selectinload(Product.options))
        .order_by(Product.sort_order)
    )
    return result.scalars().all()

@router.get("/products/{product_id}", response_model=schemas.Product)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product)
        .filter(Product.id == product_id)
        .options(selectinload(Product.options))
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# ──────────────────────────────────────────────
#  ЗАЩИЩЁННЫЕ эндпоинты (только для админа)
#  Изменение меню требует авторизации
# ──────────────────────────────────────────────

@router.post("/categories", response_model=schemas.Category)
async def create_category(
    category_data: schemas.CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    new_category = Category(**category_data.model_dump())
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category

@router.put("/categories/{category_id}", response_model=schemas.Category)
async def update_category(
    category_id: int,
    category_data: schemas.CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(Category).filter(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in category_data.model_dump().items():
        setattr(category, key, value)
    await db.commit()
    await db.refresh(category)
    return category

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(Category).filter(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(category)
    await db.commit()
    return {"message": "Category deleted successfully"}

@router.post("/products", response_model=schemas.Product)
async def create_product(
    product_data: schemas.ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    new_product = Product(**product_data.model_dump(exclude={'options'}))
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    for opt in product_data.options:
        new_option = ProductOption(
            product_id=new_product.id,
            name=opt.name,
            price=opt.price
        )
        db.add(new_option)
    await db.commit()
    result = await db.execute(
        select(Product).options(selectinload(Product.options)).filter(Product.id == new_product.id)
    )
    return result.scalar_one()

@router.put("/products/{product_id}", response_model=schemas.Product)
async def update_product(
    product_id: int,
    product_data: schemas.ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(Product).filter(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product_data.model_dump(exclude={'options'}).items():
        setattr(product, key, value)
    await db.execute(delete(ProductOption).where(ProductOption.product_id == product_id))
    for opt in product_data.options:
        new_option = ProductOption(
            product_id=product.id,
            name=opt.name,
            price=opt.price
        )
        db.add(new_option)
    await db.commit()
    result = await db.execute(
        select(Product).options(selectinload(Product.options)).filter(Product.id == product_id)
    )
    return result.scalar_one()

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(Product).filter(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.delete(product)
    await db.commit()
    return {"message": "Product deleted successfully"}
