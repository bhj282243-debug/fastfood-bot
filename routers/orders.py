import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from database import get_db
from models import Order, OrderItem, Product, User
import schemas
from bot import send_order_notification
from auth import get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/orders", response_model=schemas.Order)
async def create_order(
    order_data: schemas.OrderCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    if not order_data.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    product_ids = [item.product_id for item in order_data.items]
    result = await db.execute(select(Product).filter(Product.id.in_(product_ids)))
    products = {p.id: p for p in result.scalars().all()}

    calculated_total = 0
    order_items = []

    for item in order_data.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
        product = products.get(item.product_id)
        if not product or not product.is_available:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} not available")
        item_price = product.price
        calculated_total += item_price * item.quantity
        order_items.append(OrderItem(
            product_id=item.product_id,
            quantity=item.quantity,
            price=item_price,
            options=item.options
        ))

    calculated_total += order_data.delivery_price
    calculated_total -= order_data.discount
    calculated_total = max(calculated_total, 0)

    new_order = Order(
        customer_name=order_data.customer_name,
        phone=order_data.phone,
        address=order_data.address,
        delivery_type=order_data.delivery_type,
        delivery_price=order_data.delivery_price,
        discount=order_data.discount,
        payment_method=order_data.payment_method,
        comment=order_data.comment,
        total_price=calculated_total,
        status="new"
    )

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    for item in order_items:
        item.order_id = new_order.id
        db.add(item)

    await db.commit()

    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == new_order.id)
    )
    full_order = result.scalar_one()

    logger.info(f"Создан заказ #{full_order.id} на сумму {full_order.total_price} сум")

    # Telegram уведомление — в фоне, не блокирует ответ клиенту
    background_tasks.add_task(send_order_notification, full_order)

    return full_order


@router.get("/orders", response_model=List[schemas.Order])
async def get_orders(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    stmt = select(Order).options(selectinload(Order.items).selectinload(OrderItem.product))
    if status:
        stmt = stmt.filter(Order.status == status)
    stmt = stmt.order_by(Order.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/orders/{order_id}", response_model=schemas.Order)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/orders/{order_id}/status", response_model=schemas.Order)
async def update_order_status(
    order_id: int,
    status_update: schemas.OrderUpdateStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(Order).filter(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    old_status = order.status
    order.status = status_update.status
    await db.commit()

    logger.info(f"Заказ #{order_id}: статус {old_status} → {status_update.status} (admin: {current_user.username})")

    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == order_id)
    )
    return result.scalar_one()


@router.delete("/orders/{order_id}")
async def delete_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(Order).filter(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    await db.delete(order)
    await db.commit()
    logger.info(f"Заказ #{order_id} удалён (admin: {current_user.username})")
    return {"message": "Order deleted successfully"}
