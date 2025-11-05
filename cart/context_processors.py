# در فایل cart/context_processors.py

# from .cart import Cart

# def cart(request):
#     return {'cart': Cart(request)}
def cart(request):
    # از request.cart که توسط میدل‌ور ساخته شده استفاده کن
    return {'cart': request.cart}