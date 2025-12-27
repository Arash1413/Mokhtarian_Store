from django.shortcuts import render



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
    
    override_quantity = request.POST.get('override', 'False') == 'True'
    
    current_in_cart = cart.cart.get(str(product.id), {}).get('quantity', 0)
    
    if override_quantity:
        final_quantity = quantity
    else:
        final_quantity = current_in_cart + quantity

    error_msg = None
    
    if final_quantity > product.stock:
        error_msg = f"موجودی کافی نیست. تنها {product.stock} عدد موجود است."
        final_quantity = product.stock 

    elif final_quantity < product.min_order_quantity:
        error_msg = f"حداقل تعداد سفارش برای این محصول {product.min_order_quantity} عدد است."
        
        if override_quantity: 
             final_quantity = product.min_order_quantity

    
    elif product.max_order_quantity and final_quantity > product.max_order_quantity:
        error_msg = f"حداکثر تعداد قابل سفارش برای این محصول {product.max_order_quantity} عدد است."
        final_quantity = product.max_order_quantity

    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and error_msg:
        return JsonResponse({
            'success': False,
            'error': error_msg,
            
            'corrected_quantity': final_quantity 
        })
    
    
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest' and error_msg:
        from django.contrib import messages
        messages.error(request, error_msg)
        
        quantity = final_quantity if override_quantity else (final_quantity - current_in_cart)
        if quantity <= 0: 
             return redirect('cart:cart_detail')

    
    
    if override_quantity:
        cart.add(product=product, quantity=final_quantity, override_quantity=True)
    else:
        
        to_add = final_quantity - current_in_cart
        if to_add > 0:
            cart.add(product=product, quantity=to_add, override_quantity=False)

    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        
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
    
    cart = request.cart
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')

def cart_detail(request):
    
    cart = request.cart
    return render(request, 'cart/detail.html', {'cart': cart})