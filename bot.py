import os
from aiogram import Bot

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID")

bot = Bot(token=TOKEN) if TOKEN else None

async def send_order_notification(order):
    if not bot or not ADMIN_ID:
        return
    try:
        items_text = "\n".join([
            f"  • {item.product.name} x{item.quantity} = {item.price * item.quantity:.0f} сум"
            for item in order.items
        ])
        text = (
            f"🔔 Новый заказ #{order.id}\n\n"
            f"👤 {order.customer_name}\n"
            f"📞 {order.phone}\n"
            f"🚚 {order.delivery_type}\n"
            f"📍 {order.address or 'Самовывоз'}\n\n"
            f"📋 Состав:\n{items_text}\n\n"
            f"💰 Итого: {order.total_price:.0f} сум\n"
            f"💳 Оплата: {order.payment_method}\n"
            f"📝 Комментарий: {order.comment or 'Нет'}"
        )
        await bot.send_message(chat_id=int(ADMIN_ID), text=text)
    except Exception as e:
        print(f"Telegram ошибка: {e}")
