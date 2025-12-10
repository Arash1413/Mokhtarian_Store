from django.shortcuts import render

# Create your views here.
# در فایل cart/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from store.models import Product
from .cart import Cart

@require_POST
def cart_add(request, product_id):
    cart = request.cart
    product = get_object_or_404(Product, id=product_id)
    
    # --- تغییرات جدید: دریافت تعداد از فرم ---
    try:
        # دریافت تعداد از فرم HTML (نام فیلد name="quantity" است)
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1
    
    # همچنین چک می‌کنیم که اگر کاربر دکمه آپدیت در سبد خرید را زده بود (override)
    override_quantity = request.POST.get('override', False)
    
    cart.add(product=product, quantity=quantity, override_quantity=override_quantity)
    return redirect('cart:cart_detail')

@require_POST
def cart_remove(request, product_id):
    # cart = Cart(request)
    cart = request.cart
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')

def cart_detail(request):
    # cart = Cart(request)
    cart = request.cart
    return render(request, 'cart/detail.html', {'cart': cart})