
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
import requests
import time
from django.views.decorators.csrf import csrf_exempt

from .models import Category, Product, Order, OrderItem, ShippingAddress, Customer
from .forms import CustomUserCreationForm, ShippingForm
from cart.cart import Cart


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products_all = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products_all = products_all.filter(category=category)

    bestsellers = Product.objects.filter(available=True, is_bestseller=True)[:8]
    discounted = Product.objects.filter(available=True, old_price__isnull=False).exclude(old_price=0)[:8]
    newest = Product.objects.filter(available=True).order_by('-created')[:8]

    paginator = Paginator(products_all, 12)
    page_number = request.GET.get('page')
    products_paginated = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'categories': categories,
        'products': products_paginated,
        'bestsellers': bestsellers,
        'discounted': discounted,
        'newest': newest,
    }
    return render(request, 'store/product/list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(
        category=product.category, 
        available=True
    ).exclude(slug=slug).order_by('?')[:4]
    context = {
        'product': product,
        'related_products': related_products
    }
    return render(request, 'store/product/detail.html', context)


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required(login_url='login')
def checkout(request):
    cart = request.cart
    if len(cart) == 0:
        return redirect('store:product_list')

    if request.method == 'POST':
        form = ShippingForm(request.POST)
        if form.is_valid():
            customer = request.user.customer
            total_price_toman = cart.get_total_price()
            
            # 1. ایجاد سفارش موقت با قیمت نهایی
            order = Order.objects.create(customer=customer, complete=False, total_price=total_price_toman)
            
            # 2. ایجاد آدرس و اتصال به سفارش موقت
            shipping_address = form.save(commit=False)
            shipping_address.customer = customer
            shipping_address.order = order
            shipping_address.save()

            # 3. آماده‌سازی داده‌ها برای درگاه
            total_price_rial = int(float(total_price_toman) * 10)
            callback_url = request.build_absolute_uri(reverse('store:payment_verify'))
            pin_code = settings.MR_PARDDAKHT_API_KEY
            
            payment_data = {
                'pin': pin_code,
                'amount': total_price_rial,
                'callback': callback_url,
                'order_id': str(order.id),
                'description': f'پرداخت سفارش شماره {order.id}',
                'mobile': form.cleaned_data['phone_number'],
            }
            
            request_url = 'https://panel.aqayepardakht.ir/api/v2/create'
            headers = {'Content-Type': 'application/json'}
            
            try:
                response = requests.post(request_url, json=payment_data, headers=headers)
                response.raise_for_status() # برای خطاهای 4xx/5xx
                response_json = response.json()

                if response_json.get('status') == 'success':
                    authority = response_json.get('transid')
                    order.transaction_id = authority
                    order.save()
                    payment_url = f"https://panel.aqayepardakht.ir/startpay/{authority}"
                    return redirect(payment_url)
                else:
                    order.delete()
                    error_message = response_json.get('message', 'خطا در ایجاد تراکنش.')
                    context = {'form': form, 'cart': cart, 'error': error_message}
                    return render(request, 'store/checkout.html', context)

            except requests.exceptions.RequestException as e:
                order.delete()
                print(f"Error connecting to payment gateway: {e}")
                error_message = 'خطا در اتصال به درگاه پرداخت. لطفاً بعدا تلاش کنید.'
                context = {'form': form, 'cart': cart, 'error': error_message}
                return render(request, 'store/checkout.html', context)
    else:
        form = ShippingForm()

    context = {'form': form, 'cart': cart}
    return render(request, 'store/checkout.html', context)





def cart(request):
    # cart = Cart(request)
    cart = request.cart
    return render(request, 'cart/detail.html', {'cart': cart})


@csrf_exempt
def payment_verify(request):
    transid = request.POST.get('transid') or request.GET.get('transid')
    if not transid:
        return render(request, 'store/payment_result.html', {'error': 'تراکنش نامعتبر است.'})

    try:
        order = Order.objects.get(transaction_id=transid, complete=False)
    except Order.DoesNotExist:
        # شاید تراکنش قبلا تایید شده، دوباره چک می‌کنیم
        if Order.objects.filter(transaction_id=transid, complete=True).exists():
            final_order = Order.objects.get(transaction_id=transid)
            return render(request, 'store/payment_result.html', {'order': final_order, 'success': True, 'already_verified': True})
        return render(request, 'store/payment_result.html', {'error': 'سفارش یافت نشد.'})

    pin_code = settings.MR_PARDDAKHT_API_KEY
    amount_rial = int(float(order.total_price) * 10)
    
    verify_data = {'pin': pin_code, 'amount': amount_rial, 'transid': transid}
    verify_url = 'https://panel.aqayepardakht.ir/api/v2/verify'
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(verify_url, json=verify_data, headers=headers)
        response.raise_for_status()
        response_json = response.json()

        if response_json.get('status') == 'success':
            # نهایی کردن سفارش
            order.complete = True
            order.save()

            # اضافه کردن آیتم‌های سبد خرید به سفارش نهایی شده
            cart = request.cart
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], quantity=item['quantity'])

            # پاک کردن سبد خرید از session
            cart.clear()
            
            return render(request, 'store/payment_result.html', {'order': order, 'success': True})
        else:
            order.delete()
            error_message = response_json.get('message', 'تراکنش توسط درگاه تأیید نشد.')
            return render(request, 'store/payment_result.html', {'error': error_message})
            
    except requests.exceptions.RequestException as e:
        # در این حالت سفارش موقت را پاک نمی‌کنیم تا بعدا بتوان به صورت دستی بررسی کرد
        print(f"Error verifying payment: {e}")
        error_message = 'خطا در ارتباط با درگاه برای تأیید تراکنش. لطفاً با پشتیبانی تماس بگیرید.'
        return render(request, 'store/payment_result.html', {'error': error_message})
    

def search(request):
    query = request.GET.get('q', None)
    products = Product.objects.filter(available=True)
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    context = {
        'query': query,
        'products': products
    }
    return render(request, 'store/product/search_results.html', context)


def about_page(request):
    context = {} 
    return render(request, 'store/about.html', context)


@login_required(login_url='login')
def profile(request):
    customer = request.user.customer
    orders = Order.objects.filter(customer=customer, complete=True).order_by('-date_ordered')
    context = {
        'orders': orders
    }
    return render(request, 'store/profile.html', context)


