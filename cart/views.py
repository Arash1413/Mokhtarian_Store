from django.shortcuts import render

# Create your views here.
# در فایل cart/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from store.models import Product
from .cart import Cart
from django.http import JsonResponse

# @require_POST
# def cart_add(request, product_id):
#     cart = request.cart
#     product = get_object_or_404(Product, id=product_id)
    
#     try:
#         quantity = int(request.POST.get('quantity', 1))
#     except ValueError:
#         quantity = 1
    
#     override_quantity = request.POST.get('override', False)
    
#     # افزودن محصول به سبد
#     cart.add(product=product, quantity=quantity, override_quantity=override_quantity)

#     # --- بخش جدید: بررسی درخواست AJAX ---
#     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#         # دریافت اطلاعات جدید آیتم برای ارسال به جاوااسکریپت
#         # چون cart در سشن ذخیره شده، باید دوباره مقادیر را بخوانیم
#         item_total = 0
#         item_price = 0
#         is_wholesale = False
        
#         # محاسبه دستی مقادیر برای پاسخ JSON
#         # (چون متد __iter__ کارت فقط در تمپلیت کار می‌کند، اینجا شبیه‌سازی می‌کنیم)
#         current_item = cart.cart.get(str(product.id))
#         if current_item:
#             qty = current_item['quantity']
#             # استفاده از متد هوشمند قیمت که در مدل نوشتیم
#             current_price = product.get_current_price(qty)
#             item_total = current_price * qty
#             item_price = current_price
#             is_wholesale = (current_price == product.wholesale_price and product.wholesale_min_qty > 0)

#         return JsonResponse({
#             'success': True,
#             'item_total': f"{item_total:,.0f}", # فرمت سه رقم سه رقم
#             'item_price': f"{item_price:,.0f}",
#             'cart_total': f"{cart.get_total_price():,.0f}",
#             'cart_items_count': len(cart),
#             'is_wholesale': is_wholesale,
#             'wholesale_min': product.wholesale_min_qty,
#             'wholesale_price': f"{product.wholesale_price:,.0f}" if product.wholesale_price else 0
#         })
#     # -------------------------------------

#     return redirect('cart:cart_detail')
# cart/views.py

@require_POST
def cart_add(request, product_id):
    cart = request.cart
    product = get_object_or_404(Product, id=product_id)
    
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1
    
    override_quantity = request.POST.get('override', 'False') == 'True'
    
    # محاسبه تعداد نهایی در سبد خرید برای بررسی
    current_in_cart = cart.cart.get(str(product.id), {}).get('quantity', 0)
    
    if override_quantity:
        final_quantity = quantity
    else:
        final_quantity = current_in_cart + quantity

    # --- بررسی محدودیت‌ها ---
    error_msg = None
    
    # 1. بررسی موجودی انبار
    if final_quantity > product.stock:
        error_msg = f"موجودی کافی نیست. تنها {product.stock} عدد موجود است."
        final_quantity = product.stock # تنظیم روی حداکثر موجودی

    # 2. بررسی حداقل سفارش
    elif final_quantity < product.min_order_quantity:
        error_msg = f"حداقل تعداد سفارش برای این محصول {product.min_order_quantity} عدد است."
        # در حالت override نباید اجازه دهیم کمتر شود، اما در حالت افزودن شاید کاربر بخواهد کم کم اضافه کند
        # معمولاً سخت‌گیرانه عمل می‌کنیم:
        if override_quantity: 
             final_quantity = product.min_order_quantity

    # 3. بررسی حداکثر سفارش (اگر محدودیت تعیین شده باشد)
    elif product.max_order_quantity and final_quantity > product.max_order_quantity:
        error_msg = f"حداکثر تعداد قابل سفارش برای این محصول {product.max_order_quantity} عدد است."
        final_quantity = product.max_order_quantity

    # اگر درخواست AJAX بود و خطایی داشتیم، ارور را برگردان
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and error_msg:
        return JsonResponse({
            'success': False,
            'error': error_msg,
            # مقدار مجاز را برمی‌گردانیم تا در input اصلاح شود
            'corrected_quantity': final_quantity 
        })
    
    # اگر درخواست معمولی بود و خطا داشتیم (مثلا از صفحه محصول)
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest' and error_msg:
        from django.contrib import messages
        messages.error(request, error_msg)
        # در صورت خطا در افزودن معمولی، عملیات را متوقف می‌کنیم یا با مقدار اصلاح شده ادامه می‌دهیم
        # اینجا با مقدار اصلاح شده ادامه می‌دهیم:
        quantity = final_quantity if override_quantity else (final_quantity - current_in_cart)
        if quantity <= 0: # اگر با اصلاحیه، چیزی برای افزودن نماند
             return redirect('cart:cart_detail')

    # افزودن به سبد (با مقدار تایید شده یا اصلاح شده)
    # اگر در لاجیک بالا quantity تغییر کرد، اینجا اعمال می‌شود
    # اما چون cart.add منطق خودش را دارد، ما مقدار اصلاح شده نهایی را پاس می‌دهیم
    
    if override_quantity:
        cart.add(product=product, quantity=final_quantity, override_quantity=True)
    else:
        # برای حالت افزودن، باید ما‌به‌التفاوت را اضافه کنیم چون cart.add جمع می‌زند
        to_add = final_quantity - current_in_cart
        if to_add > 0:
            cart.add(product=product, quantity=to_add, override_quantity=False)

    # --- بخش AJAX (موفق) ---
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # محاسبات پاسخ JSON (مثل قبل)
        current_item = cart.cart.get(str(product.id))
        item_total = 0
        item_price = 0
        is_wholesale = False
        
        if current_item:
            qty = current_item['quantity']
            current_price = product.get_current_price(qty)
            item_total = current_price * qty
            item_price = current_price
            is_wholesale = (current_price == product.wholesale_price and product.wholesale_min_qty > 0)

        return JsonResponse({
            'success': True,
            'item_total': f"{item_total:,.0f}",
            'item_price': f"{item_price:,.0f}",
            'cart_total': f"{cart.get_total_price():,.0f}",
            'cart_items_count': len(cart),
            'is_wholesale': is_wholesale,
            'wholesale_min': product.wholesale_min_qty,
            'wholesale_price': f"{product.wholesale_price:,.0f}" if product.wholesale_price else 0
        })

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