# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib.auth import login
# from django.contrib.auth.decorators import login_required
# from django.urls import reverse
# from django.conf import settings
# from django.core.paginator import Paginator
# from django.db.models import Q
# import requests
# import time # <-- ایمپورت جدید

# from .models import Category, Product, Order, OrderItem, ShippingAddress, Customer
# from .forms import CustomUserCreationForm, ShippingForm
# from cart.cart import Cart

# def product_list(request, category_slug=None):
#     category = None
#     categories = Category.objects.all()
#     products_all = Product.objects.filter(available=True)

#     if category_slug:
#         category = get_object_or_404(Category, slug=category_slug)
#         products_all = products_all.filter(category=category)

#     bestsellers = Product.objects.filter(available=True, is_bestseller=True)[:8]
#     discounted = Product.objects.filter(available=True, old_price__isnull=False).exclude(old_price=0)[:8]
#     newest = Product.objects.filter(available=True).order_by('-created')[:8]

#     paginator = Paginator(products_all, 12)
#     page_number = request.GET.get('page')
#     products_paginated = paginator.get_page(page_number)
    
#     context = {
#         'category': category,
#         'categories': categories,
#         'products': products_paginated,
#         'bestsellers': bestsellers,
#         'discounted': discounted,
#         'newest': newest,
#     }
#     return render(request, 'store/product/list.html', context)

# def product_detail(request, slug):
#     product = get_object_or_404(Product, slug=slug, available=True)
#     related_products = Product.objects.filter(
#         category=product.category, 
#         available=True
#     ).exclude(slug=slug).order_by('?')[:4]
#     context = {
#         'product': product,
#         'related_products': related_products
#     }
#     return render(request, 'store/product/detail.html', context)

# def register(request):
#     if request.method == 'POST':
#         form = CustomUserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)
#             return redirect('/')
#     else:
#         form = CustomUserCreationForm()
#     return render(request, 'registration/register.html', {'form': form})

# # ==============================================================================
# # تابع CHECKOUT بازنویسی شده
# # ==============================================================================
# @login_required(login_url='login')
# def checkout(request):
#     cart = Cart(request)
#     if len(cart) == 0:
#         return redirect('store:product_list')

#     if request.method == 'POST':
#         form = ShippingForm(request.POST)
#         if form.is_valid():
#             # اطلاعات فرم را در session ذخیره می‌کنیم به جای ساخت سفارش
#             shipping_info_data = {
#                 'full_name': form.cleaned_data['full_name'],
#                 'phone_number': form.cleaned_data['phone_number'],
#                 'address': form.cleaned_data['address'],
#                 'city': form.cleaned_data['city'],
#                 'state': form.cleaned_data['state'],
#                 'zipcode': form.cleaned_data['zipcode'],
#             }
#             # حالا این دیکشنری تمیز را در session ذخیره می‌کنیم
#             request.session['shipping_info'] = shipping_info_data

#             total_price_rial = int(cart.get_total_price() * 10)
#             callback_url = request.build_absolute_uri(reverse('store:payment_verify'))
#             pin_code = settings.MR_PARDDAKHT_API_KEY
            
#             # یک شناسه موقت برای تراکنش می‌سازیم
#             temp_invoice_id = str(int(time.time()))

#             payment_data = {
#                 'pin': "sandbox", # یا pin_code برای حالت واقعی
#                 'amount': total_price_rial,
#                 'callback': callback_url,
#                 'invoice_id': temp_invoice_id, 
#                 'description': f'پرداخت سفارش از فروشگاه MELO',
#             }
            
#             request_url = 'https://panel.aqayepardakht.ir/api/v2/create'
            
#             try:
#                 response = requests.post(request_url, json=payment_data)
#                 response.raise_for_status()
#                 response_json = response.json()
#                 if response_json.get('status') == 'success':
#                     authority = response_json.get('transid')
#                     # authority را در session ذخیره می‌کنیم برای تایید بعدی
#                     request.session['payment_authority'] = authority
#                     payment_url = f"https://panel.aqayepardakht.ir/startpay/sandbox/{authority}"
#                     return redirect(payment_url)
#                 else:
#                     error_message = response_json.get('message', 'خطا در ایجاد تراکنش.')
#                     return render(request, 'cart/detail.html', {'error': error_message})
#             except requests.exceptions.RequestException as e:
#                 print(f"Error connecting to payment gateway: {e}")
#                 error_message = 'خطا در اتصال به درگاه پرداخت. لطفاً لحظاتی دیگر تلاش کنید.'
#                 return render(request, 'cart/detail.html', {'error': error_message})
            
#     else:
#         form = ShippingForm()

#     context = {'form': form, 'cart': cart}
#     return render(request, 'store/checkout.html', context)

# def cart(request):
#     cart = Cart(request)
#     return render(request, 'cart/detail.html', {'cart': cart})

# # ==============================================================================
# # تابع PAYMENT_VERIFY بازنویسی شده
# # ==============================================================================
# def payment_verify(request):
#     transid = request.GET.get('transid')
#     authority_from_session = request.session.get('payment_authority')

#     if not transid or transid != authority_from_session:
#         return render(request, 'store/payment_result.html', {'error': 'تراکنش نامعتبر است.'})

#     cart = Cart(request)
#     shipping_info = request.session.get('shipping_info')

#     if not cart or not shipping_info:
#         return render(request, 'store/payment_result.html', {'error': 'اطلاعات سفارش یافت نشد، ممکن است نشست شما منقضی شده باشد.'})

#     amount_rial = int(cart.get_total_price() * 10)
#     pin_code = settings.MR_PARDDAKHT_API_KEY
    
#     verify_data = {
#         'pin': "sandbox", # یا pin_code برای حالت واقعی
#         'amount': amount_rial, 
#         'transid': transid
#     }
#     verify_url = 'https://panel.aqayepardakht.ir/api/v2/verify'
    
#     try:
#         response = requests.post(verify_url, json=verify_data)
#         response.raise_for_status()
#         response_json = response.json()

#         if response_json.get('status') == 'success':
#             # پرداخت موفق! حالا سفارش را در دیتابیس ایجاد می‌کنیم
#             customer = request.user.customer
#             order = Order.objects.create(
#                 customer=customer, 
#                 complete=True,
#                 transaction_id=transid
#             )
#             for item in cart:
#                 OrderItem.objects.create(
#                     order=order, product=item['product'], quantity=item['quantity']
#                 )
#             ShippingAddress.objects.create(
#                 customer=customer,
#                 order=order,
#                 **shipping_info
#             )

#             # پاک کردن سبد خرید و اطلاعات موقت از session
#             cart.clear()
#             del request.session['shipping_info']
#             del request.session['payment_authority']
            
#             return render(request, 'store/payment_result.html', {'order': order, 'success': True})
#         else:
#             error_message = response_json.get('message', 'تراکنش توسط درگاه تأیید نشد.')
#             return render(request, 'store/payment_result.html', {'error': error_message})

#     except requests.exceptions.RequestException as e:
#         print(f"Error verifying payment: {e}")
#         error_message = 'خطا در ارتباط با درگاه برای تأیید تراکنش.'
#         return render(request, 'store/payment_result.html', {'error': error_message})

# def search(request):
#     query = request.GET.get('q', None)
#     products = Product.objects.filter(available=True)
#     if query:
#         products = products.filter(
#             Q(name__icontains=query) | 
#             Q(description__icontains=query)
#         )
#     context = {
#         'query': query,
#         'products': products
#     }
#     return render(request, 'store/product/search_results.html', context)

# def about_page(request):
#     context = {} 
#     return render(request, 'store/about.html', context)

# @login_required(login_url='login')
# def profile(request):
#     customer = request.user.customer
#     orders = Order.objects.filter(customer=customer, complete=True).order_by('-date_ordered')
#     context = {
#         'orders': orders
#     }
#     return render(request, 'store/profile.html', context)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
import requests
import time

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
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('store:product_list')

    if request.method == 'POST':
        form = ShippingForm(request.POST)
        if form.is_valid():
            # اطلاعات فرم را به صورت یک دیکشنری تمیز در session ذخیره می‌کنیم
            shipping_info_data = {
                'full_name': form.cleaned_data['full_name'],
                'phone_number': form.cleaned_data['phone_number'],
                'address': form.cleaned_data['address'],
                'city': form.cleaned_data['city'],
                'state': form.cleaned_data['state'],
                'zipcode': form.cleaned_data['zipcode'],
            }
            request.session['shipping_info'] = shipping_info_data

            total_price_rial = int(cart.get_total_price() * 10)
            callback_url = request.build_absolute_uri(reverse('store:payment_verify'))
            pin_code = settings.MR_PARDDAKHT_API_KEY
            
            temp_invoice_id = str(int(time.time()))

            payment_data = {
                            "pin": "sandbox",
                "amount": 28000,
                "callback": "https://yourdomain.com/payment/verify/",
                "invoice_id": "order-1234",
                "description": "خرید از فروشگاه من",
                "mobile": "09123456789",
                "email": "user@example.com",
                "card_number": "1234123412341234"
                        }
            
            request_url = 'https://panel.aqayepardakht.ir/api/v2/create'
            
            try:
                response = requests.post(request_url, json=payment_data)
                response.raise_for_status()
                response_json = response.json()

                if response_json.get('status') == 'success':
                    authority = response_json.get('transid')
                    request.session['payment_authority'] = authority
                    payment_url = f"https://panel.aqayepardakht.ir/startpay/sandbox/{authority}"
                    return redirect(payment_url)
                else:
                    error_message = response_json.get('message', 'خطا در ایجاد تراکنش.')
                    # می‌توانید پیام خطا را به context اضافه کرده و در checkout.html نمایش دهید
                    context = {'form': form, 'cart': cart, 'error': error_message}
                    return render(request, 'store/checkout.html', context)

            except requests.exceptions.RequestException as e:
                print(f"Error connecting to payment gateway: {e}")
                error_message = 'خطا در اتصال به درگاه پرداخت. لطفاً لحظاتی دیگر تلاش کنید.'
                context = {'form': form, 'cart': cart, 'error': error_message}
                return render(request, 'store/checkout.html', context)
            
    else: # اگر متد GET بود
        form = ShippingForm()

    context = {'form': form, 'cart': cart}
    return render(request, 'store/checkout.html', context)


def cart(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})


def payment_verify(request):
    transid = request.GET.get('transid')
    authority_from_session = request.session.get('payment_authority')

    if not transid or transid != authority_from_session:
        return render(request, 'store/payment_result.html', {'error': 'تراکنش نامعتبر است.'})

    cart = Cart(request)
    shipping_info = request.session.get('shipping_info')

    if not cart or not shipping_info:
        return render(request, 'store/payment_result.html', {'error': 'اطلاعات سفارش یافت نشد، ممکن است نشست شما منقضی شده باشد.'})

    amount_rial = int(cart.get_total_price() * 10)
    pin_code = settings.MR_PARDDAKHT_API_KEY
    
    verify_data = {
        'pin': "sandbox",  # برای حالت واقعی به pin_code تغییر دهید
        'amount': amount_rial, 
        'transid': transid
    }
    verify_url = 'https://panel.aqayepardakht.ir/api/v2/verify'
    
    try:
        response = requests.post(verify_url, json=verify_data)
        response.raise_for_status()
        response_json = response.json()

        if response_json.get('status') == 'success':
            customer = request.user.customer
            order = Order.objects.create(
                customer=customer, 
                complete=True,
                transaction_id=transid
            )
            for item in cart:
                OrderItem.objects.create(
                    order=order, product=item['product'], quantity=item['quantity']
                )
            ShippingAddress.objects.create(
                customer=customer,
                order=order,
                **shipping_info
            )

            cart.clear()
            del request.session['shipping_info']
            del request.session['payment_authority']
            
            return render(request, 'store/payment_result.html', {'order': order, 'success': True})
        else:
            error_message = response_json.get('message', 'تراکنش توسط درگاه تأیید نشد.')
            return render(request, 'store/payment_result.html', {'error': error_message})

    except requests.exceptions.RequestException as e:
        print(f"Error verifying payment: {e}")
        error_message = 'خطا در ارتباط با درگاه برای تأیید تراکنش.'
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