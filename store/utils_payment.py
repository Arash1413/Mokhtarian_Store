import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# جدول کدهای خطای آقای پرداخت
PAYMENT_ERROR_CODES = {
    -1: 'amount نمی‌تواند خالی باشد',
    -2: 'کد پین درگاه نمی‌تواند خالی باشد',
    -3: 'callback نمی‌تواند خالی باشد',
    -4: 'amount باید عددی باشد',
    -5: 'amount باید بین 1,000 تا 200,000,000 تومان باشد',
    -6: 'کد پین درگاه اشتباه هست',
    -7: 'transid نمی‌تواند خالی باشد',
    -8: 'تراکنش مورد نظر وجود ندارد',
    -9: 'کد پین درگاه با درگاه تراکنش مطابقت ندارد',
    -10: 'مبلغ با مبلغ تراکنش مطابقت ندارد',
    -11: 'درگاه در انتظار تأیید و یا غیرفعال است',
    -12: 'امکان ارسال درخواست برای این پذیرنده وجود ندارد',
    -13: 'شماره کارت باید 16 رقم چسبیده بهم باشد',
    -14: 'درگاه بر روی سایت دیگری درحال استفاده است',
    -15: 'آدرس کال‌بک ارسال شده با دامنه تأیید شده درگاه پرداخت مغایرت دارد',
}

def debug_prepare_payment_data(payment_data: dict) -> None:
    required_keys = ['pin', 'amount', 'callback', 'order_id', 'description']
    for key in required_keys:
        if key not in payment_data:
            logger.error(f"[PaymentDebug] Missing required parameter: {key}")
        elif payment_data.get(key) in (None, '', []):
            logger.error(f"[PaymentDebug] Parameter '{key}' is empty: {payment_data.get(key)}")

    amount = payment_data.get('amount')
    try:
        amount_int = int(amount)
        if amount_int < 1000 or amount_int > 200_000_000:
            logger.warning(f"[PaymentDebug] Amount {amount_int} outside allowed range (1,000-200,000,000)")
    except (ValueError, TypeError):
        logger.error(f"[PaymentDebug] Amount is not a valid integer: {amount}")

    pin = payment_data.get('pin')
    if pin == settings.MR_PARDDAKHT_API_KEY:
        logger.info("[PaymentDebug] Pin is correct.")
    else:
        logger.warning(f"[PaymentDebug] Pin may be incorrect: {pin}")

    callback = payment_data.get('callback')
    if not isinstance(callback, str) or not callback.startswith('https://'):
        logger.warning(f"[PaymentDebug] Callback URL does not look secure: {callback}")

    logger.info(f"[PaymentDebug] Prepared payment data: order_id={payment_data.get('order_id')}, amount={payment_data.get('amount')}")

def debug_handle_response(response_json: dict) -> None:
    status = response_json.get('status')
    if status == 'success':
        logger.info(f"[PaymentDebug] Payment response OK: {response_json}")
    else:
        code = response_json.get('code')
        message = response_json.get('message', '')
        human_msg = PAYMENT_ERROR_CODES.get(code, 'کد خطای ناشناخته')
        logger.error(f"[PaymentDebug] Payment failed: code={code}, message='{message}', meaning='{human_msg}'")
