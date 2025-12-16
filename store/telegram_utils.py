# store/telegram_utils.py
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_bale_order_notification(order):
    """
    ارسال پیام به پیام‌رسان بله (بدون نیاز به فیلترشکن)
    """
    # توکن ربات بله را در settings.py اضافه کنید: BALE_BOT_TOKEN
    token = settings.BALE_BOT_TOKEN 
    chat_id = settings.BALE_ADMIN_CHAT_ID
    
    message = (
        f"✅ **سفارش جدید ثبت شد!**\n"
        f"💰 مبلغ: {int(order.total_price):,} تومان\n"
        f"👤 مشتری: {order.customer.name}\n"
        f"🆔 شناسه: {order.id}"
    )

    # آدرس API بله (تفاوت اصلی با تلگرام همینجاست)
    url = f"https://tapi.bale.ai/bot{token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
    }

    try:
        # اینجا دیگر نیازی به proxies نداریم چون بله فیلتر نیست
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            logger.error(f"Bale Notification Failed: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Bale message: {e}")