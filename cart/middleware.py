# در فایل cart/middleware.py

from .cart import Cart

class CartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # این کد قبل از اجرای view اجرا می‌شود
        request.cart = Cart(request)
        
        response = self.get_response(request)
        
        # این کد بعد از اجرای view اجرا می‌شود (اگر نیاز بود)
        return response