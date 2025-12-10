from django.shortcuts import render

# Create your views here.
# در فایل cart/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from store.models import Product
from .cart import Cart
from django.http import JsonResponse

@require_POST
def cart_add(request, product_id):
    cart = request.cart
    product = get_object_or_404(Product, id=product_id)
    
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1
    
    override_quantity = request.POST.get('override', False)
    
    # افزودن محصول به سبد
    cart.add(product=product, quantity=quantity, override_quantity=override_quantity)

    # --- بخش جدید: بررسی درخواست AJAX ---
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # دریافت اطلاعات جدید آیتم برای ارسال به جاوااسکریپت
        # چون cart در سشن ذخیره شده، باید دوباره مقادیر را بخوانیم
        item_total = 0
        item_price = 0
        is_wholesale = False
        
        # محاسبه دستی مقادیر برای پاسخ JSON
        # (چون متد __iter__ کارت فقط در تمپلیت کار می‌کند، اینجا شبیه‌سازی می‌کنیم)
        current_item = cart.cart.get(str(product.id))
        if current_item:
            qty = current_item['quantity']
            # استفاده از متد هوشمند قیمت که در مدل نوشتیم
            current_price = product.get_current_price(qty)
            item_total = current_price * qty
            item_price = current_price
            is_wholesale = (current_price == product.wholesale_price and product.wholesale_min_qty > 0)

        return JsonResponse({
            'success': True,
            'item_total': f"{item_total:,.0f}", # فرمت سه رقم سه رقم
            'item_price': f"{item_price:,.0f}",
            'cart_total': f"{cart.get_total_price():,.0f}",
            'cart_items_count': len(cart),
            'is_wholesale': is_wholesale,
            'wholesale_min': product.wholesale_min_qty,
            'wholesale_price': f"{product.wholesale_price:,.0f}" if product.wholesale_price else 0
        })
    # -------------------------------------

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