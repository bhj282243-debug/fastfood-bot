import os
import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID")

TIMEOUT = httpx.Timeout(10.0, connect=5.0)
MAX_RETRIES = 3


async def send_order_notification(order):
    if not TOKEN or not ADMIN_ID:
        logger.warning("Telegram не настроен: TELEGRAM_BOT_TOKEN или ADMIN_TELEGRAM_ID не заданы")
        return

    delivery_label = {
        "delivery": "🚚 Доставка",
        "pickup": "🏃 Самовывоз",
    }.get(order.delivery_type, order.delivery_type)

    payment_label = {
        "cash": "💵 Наличные",
        "card": "💳 Карта",
        "online": "📱 Онлайн",
    }.get(order.payment_method, order.payment_method)

    items_text = "\n".join([
        f"  • {item.product.name} × {item.quantity} = {item.price * item.quantity:,.0f} сум"
        for item in order.items
    ])

    text = (
        f"🔔 *Новый заказ #{order.id}*\n\n"
        f"👤 {order.customer_name}\n"
        f"📞 {order.phone}\n"
        f"{delivery_label}\n"
        f"📍 {order.address or 'Самовывоз'}\n\n"
        f"📋 *Состав:*\n{items_text}\n\n"
        f"💰 *Итого: {order.total_price:,.0f} сум*\n"
        f"{payment_label}\n"
        f"📝 {order.comment or 'Без комментария'}"
    )

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": int(ADMIN_ID),
        "text": text,
        "parse_mode": "Markdown",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    logger.info(f"Telegram уведомление отправлено: заказ #{order.id}")
                    return
                else:
                    logger.warning(
                        f"Telegram вернул {response.status_code} (попытка {attempt}/{MAX_RETRIES}): "
                        f"{response.text[:200]}"
                    )
        except httpx.TimeoutException:
            logger.warning(f"Telegram timeout (попытка {attempt}/{MAX_RETRIES}): заказ #{order.id}")
        except httpx.RequestError as e:
            logger.warning(f"Telegram сетевая ошибка (попытка {attempt}/{MAX_RETRIES}): {e}")
        except Exception as e:
            logger.error(f"Telegram неожиданная ошибка: {e}", exc_info=True)
            return

        if attempt < MAX_RETRIES:
            await asyncio.sleep(1)

    logger.error(f"Telegram уведомление не отправлено после {MAX_RETRIES} попыток: заказ #{order.id}")
