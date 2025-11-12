# در فایل cart/context_processors.py


def cart(request):
    # از request.cart که توسط میدل‌ور ساخته شده استفاده کن
    return {'cart': request.cart}