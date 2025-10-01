from django.shortcuts import render

# Create your views here.
# در فایل cart/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from store.models import Product
from .cart import Cart

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    # اینجا می‌توانید فرمی برای دریافت تعداد داشته باشید، فعلاً ساده کار می‌کنیم
    quantity = 1 # فعلاً همیشه یک عدد اضافه می‌کنیم
    cart.add(product=product, quantity=quantity)
    return redirect('cart:cart_detail')

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})