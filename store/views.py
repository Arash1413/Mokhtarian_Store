


from asyncio.log import logger
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
import requests
import random
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Category, Product, Order, OrderItem, ShippingAddress, Customer
from .forms import CustomUserCreationForm, ShippingForm
from cart.cart import Cart
from .utils_payment import debug_prepare_payment_data, debug_handle_response
from django.contrib.auth import login
from .utils_shipping import calculate_shipping_cost
import logging
logger = logging.getLogger(__name__)
# ==============================================================================
# VIEWS مربوط به نمایش محصولات و صفحات عمومی (بدون تغییر)
# ==============================================================================

def product_list(request, category_slug=None):
    category = None
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
        'category': category, 'products': products_paginated,
        'bestsellers': bestsellers, 'discounted': discounted, 'newest': newest,
    }
    return render(request, 'store/product/list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(category=product.category, available=True).exclude(slug=slug).order_by('?')[:4]
    context = {'product': product, 'related_products': related_products}
    return render(request, 'store/product/detail.html', context)

def search(request):
    query = request.GET.get('q', None)
    products = Product.objects.filter(available=True)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    context = {'query': query, 'products': products}
    return render(request, 'store/product/search_results.html', context)

def about_page(request):
    return render(request, 'store/about.html', {})

def cart(request):
    return render(request, 'cart/detail.html', {'cart': request.cart})

# ==============================================================================
# VIEWS مربوط به ثبت نام سنتی (برای کاربرانی که می‌خواهند حساب دائمی داشته باشند)
# ==============================================================================

def register(request):
    # اگر کاربر لاگین است، اجازه دسترسی نده
    if request.user.is_authenticated:
        return redirect('store:product_list')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # 1. ساخت یوزر اصلی جنگو
            user = form.save()
            
            # 2. دریافت شماره موبایل پاک‌سازی شده از فرم
            phone = form.cleaned_data.get('phone_number')

            # 3. ایجاد یا آپدیت مدل Customer با شماره موبایل
            # نکته: ما از get_or_create استفاده می‌کنیم تا اگر رکوردی ناقص وجود داشت، هندل شود
            customer, created = Customer.objects.get_or_create(
                user=user,
                defaults={
                    'name': user.username,
                    'phone_number': phone
                }
            )
            
            # اگر مشتری از قبل وجود داشت (که بعید است چون یوزر تازه ساخته شده) اما محض اطمینان آپدیت می‌کنیم
            if not created:
                customer.phone_number = phone
                customer.save()

            # 4. ورود خودکار کاربر
            login(request, user)
            return redirect('/')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

# ==============================================================================
# VIEWS مربوط به فرآیند OTP (کد نهایی و صحیح)
# ==============================================================================

def otp_page(request):
    # شماره موبایلی که در مرحله Checkout وارد شده را می‌گیریم
    phone = request.session.get('pending_phone')
    if not phone:
        messages.error(request, "لطفاً ابتدا اطلاعات ارسال را تکمیل کنید.")
        return redirect('store:checkout')
        
    return render(request, 'store/otp_page.html', {'phone': phone})

@csrf_exempt
def send_otp(request):
    if request.method == "POST":
        phone = request.POST.get("phone")
        if not phone:
            return JsonResponse({"error": "شماره موبایل الزامی است."}, status=400)

        if cache.get(f"otp_sent_{phone}"):
            return JsonResponse({"error": "کد قبلاً ارسال شده است. لطفاً ۲ دقیقه صبر کنید."}, status=429)

        otp = str(random.randint(100000, 999999))
        cache_key = f"otp_{phone}"
        cache.set(cache_key, otp, timeout=120)
        cache.set(f"otp_sent_{phone}", True, timeout=120)

        url = "https://api.sms.ir/v1/send/verify"
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "x-api-key": settings.SMS_IR_API_KEY
        }
        payload = {
            "mobile": phone,
            "templateId": settings.SMS_IR_TEMPLATE_ID,
            "parameters": [{"name": "Code", "value": otp}]
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            if response_data.get('status') == 1:
                return JsonResponse({"message": "کد تأیید با موفقیت ارسال شد."})
            else:
                error_message = response_data.get('message', 'خطای نامشخص از سرویس پیامک.')
                print(f"SMS.ir API Error: {error_message}")
                return JsonResponse({"error": f"خطا در ارسال پیامک: {error_message}"}, status=500)
        except requests.exceptions.RequestException as e:
            print(f"SMS sending request error: {e}")
            return JsonResponse({"error": "خطا در برقراری ارتباط با سرویس پیامک."}, status=500)
            
    return JsonResponse({"error": "درخواست نامعتبر."}, status=405)


@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        # 1. دریافت اطلاعات از درخواست یا سشن
        phone = request.POST.get("phone") or request.session.get('pending_phone')
        code = request.POST.get("code")

        if not phone or not code:
            return JsonResponse({"success": False, "message": "اطلاعات ناقص است."}, status=400)

        # 2. بررسی صحت کد OTP
        saved_code = cache.get(f"otp_{phone}")
        
        if saved_code and str(saved_code) == str(code):
            # --- کد صحیح است: شروع فرآیند ثبت سفارش ---
            
            # پاک کردن کد از کش برای جلوگیری از استفاده مجدد
            cache.delete(f"otp_{phone}")
            
            # دریافت اطلاعات سبد خرید و آدرس از سشن
            cart = request.cart
            shipping_data = request.session.get('shipping_data')
            
            if not shipping_data or len(cart) == 0:
                return JsonResponse({
                    "success": False, 
                    "message": "اطلاعات سبد خرید یا آدرس یافت نشد. لطفاً مجدد تلاش کنید.",
                    "redirect_url": reverse('store:checkout')
                })

            try:
                # 3. پیدا کردن یا ساختن مشتری
                full_name = shipping_data.get('full_name', f"کاربر {phone}")
                customer, created = Customer.objects.get_or_create(
                    phone_number=phone,
                    defaults={'name': full_name}
                )
                
                if not created and not customer.name:
                    customer.name = full_name
                    customer.save()

                # 4. --- محاسبه هزینه ارسال و مبلغ نهایی (بخش جدید) ---
                shipping_method = shipping_data.get('shipping_method', 'mahex') # پیش‌فرض ماهکس
                total_weight = cart.get_total_weight()
                cart_total_price = cart.get_total_price()
                
                final_shipping_cost = 0 # هزینه ارسال پیش‌فرض (برای ماهکس یا پس‌کرایه 0 است)

                if shipping_method == 'post':
                    # محاسبه هزینه پست بر اساس وزن
                    final_shipping_cost = calculate_shipping_cost(total_weight)
                
                # قیمت نهایی = قیمت کالاها + هزینه ارسال
                final_total_price = float(cart_total_price) + float(final_shipping_cost)

                # 5. ایجاد سفارش (با ذخیره جزئیات ارسال)
                order = Order.objects.create(
                    customer=customer, 
                    complete=False, 
                    total_price=final_total_price, # قیمت نهایی شامل پست
                    shipping_method=shipping_method,
                    shipping_cost=final_shipping_cost,
                    status='pending'
                )

                # 6. ایجاد آیتم‌های سفارش
                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        quantity=item['quantity'],
                        price=item['price'] # قیمت محاسبه شده (عمده یا عادی) را ذخیره کن
                    )

                # 7. ذخیره آدرس در دیتابیس
                ShippingAddress.objects.create(
                    customer=customer,
                    order=order,
                    full_name=shipping_data.get('full_name'),
                    phone_number=shipping_data.get('phone_number'),
                    address=shipping_data.get('address'),
                    city=shipping_data.get('city'),
                    state=shipping_data.get('state'),
                    zipcode=shipping_data.get('zipcode')
                )

                # 8. اتصال به درگاه پرداخت
                # تبدیل تومان به ریال برای درگاه (ضرب در 10)
                amount_toman = int(final_total_price)
                callback_url = request.build_absolute_uri(reverse('store:payment_verify'))
                
                payment_data = {
                    'pin': settings.MR_PARDDAKHT_API_KEY,
                    'amount': amount_toman,
                    'callback': callback_url,
                    'order_id': str(order.id),
                    'description': f'پرداخت سفارش شماره {order.id} | ارسال: {shipping_method}',
                    'mobile': phone,
                }

                # لاگ کردن برای دیباگ
                debug_prepare_payment_data(payment_data)

                request_url = 'https://panel.aqayepardakht.ir/api/v2/create'
                headers = {'Content-Type': 'application/json'}

                response = requests.post(request_url, json=payment_data, headers=headers, timeout=10)
                response.raise_for_status()
                response_json = response.json()
                
                # لاگ پاسخ درگاه
                debug_handle_response(response_json)

                if response_json.get('status') == 'success':
                    transid = response_json.get('transid')
                    order.transaction_id = transid
                    order.save()
                    
                    # پاک کردن داده‌های موقت سشن (به جز phone_verified که شاید برای صفحه بعد لازم شود)
                    del request.session['shipping_data']
                    
                    payment_url = f"https://panel.aqayepardakht.ir/startpay/{transid}"
                    return JsonResponse({
                        "success": True, 
                        "message": "در حال انتقال به درگاه پرداخت...",
                        "redirect_url": payment_url
                    })
                else:
                    order.delete()
                    logger.error(f"Payment creation failed: {response_json}")
                    return JsonResponse({
                        "success": False, 
                        "message": f"خطا در درگاه پرداخت: {response_json.get('message', 'خطای ناشناخته')}"
                    })

            except Exception as e:
                # اگر خطایی رخ داد، سفارش ناقص را پاک کن
                if 'order' in locals() and order.id:
                    order.delete()
                logger.exception("Error processing verify_otp order creation")
                print(f"Error processing order: {e}")
                return JsonResponse({
                    "success": False, 
                    "message": "خطا در ثبت سفارش. لطفاً دقایقی دیگر تلاش کنید."
                })

        else:
            return JsonResponse({"success": False, "message": "کد وارد شده نادرست یا منقضی شده است."})
    
    return JsonResponse({"error": "درخواست نامعتبر."}, status=405)

# ==============================================================================
# VIEWS مربوط به فرآیند خرید و پرداخت (کد نهایی و صحیح)
# ==============================================================================

def checkout(request):
    cart = request.cart
    if len(cart) == 0:
        return redirect('store:product_list')

    # محاسبه وزن و هزینه پست برای نمایش در صفحه
    total_weight = cart.get_total_weight()
    shipping_cost_post = calculate_shipping_cost(total_weight)

    if request.method == 'POST':
        form = ShippingForm(request.POST)
        if form.is_valid():
            shipping_data = form.cleaned_data
            phone_number = shipping_data.get('phone_number')
            
            # دریافت روش ارسال انتخاب شده از فرم
            selected_method = request.POST.get('shipping_method') # mahex یا post
            
            # ذخیره در سشن
            request.session['shipping_data'] = shipping_data
            request.session['shipping_data']['shipping_method'] = selected_method # ذخیره روش ارسال
            request.session['pending_phone'] = phone_number
            
            return redirect('store:otp_page')
    else:
        saved_data = request.session.get('shipping_data')
        form = ShippingForm(initial=saved_data) if saved_data else ShippingForm()

    context = {
        'form': form, 
        'cart': cart,
        'shipping_cost_post': shipping_cost_post, # ارسال هزینه پست به قالب
        'total_weight': total_weight
    }
    return render(request, 'store/checkout.html', context)


@csrf_exempt
def payment_verify(request):
    transid = request.POST.get('transid') or request.GET.get('transid')
    if not transid:
        logger.error("verify called without transid")
        return render(request, 'store/payment_result.html', {'error': 'تراکنش نامعتبر است.'})

    try:
        order = Order.objects.get(transaction_id=transid, complete=False)
    except Order.DoesNotExist:
        if Order.objects.filter(transaction_id=transid, complete=True).exists():
            order_done = Order.objects.get(transaction_id=transid)
            return render(request, 'store/payment_result.html', {'order': order_done, 'success': True, 'already_verified': True})
        logger.error(f"Order with transid {transid} not found") 
        return render(request, 'store/payment_result.html', {'error': 'سفارش یافت نشد.'})

    verify_data = {'pin': settings.MR_PARDDAKHT_API_KEY, 'amount': int(float(order.total_price) * 10), 'transid': transid}

    debug_prepare_payment_data(verify_data)

    verify_url = 'https://panel.aqayepardakht.ir/api/v2/verify'
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(verify_url, json=verify_data, headers=headers, timeout=10)
        response.raise_for_status()
        response_json = response.json()

        logger.info(f"Payment verify response: {response_json}")
        if response_json.get('status') == 'success':
            order.complete = True
            order.status = 'paid'
            order.save()
            request.cart.clear()
            request.session.pop('phone_verified', None) # پاک کردن سشن بعد از خرید موفق
            request.session.pop('next_url', None)
            return render(request, 'store/payment_result.html', {'order': order, 'success': True})
        else:
            error_message = response_json.get('message', 'تراکنش توسط درگاه تأیید نشد.')
            logger.error(f"Payment verification failed: {response_json}")
            order.delete()
            return render(request, 'store/payment_result.html', {'error': error_message})
    except requests.exceptions.RequestException as e:
        logger.exception("Error verifying payment with gateway")
        print(f"Error verifying payment: {e}")
        error_message = 'خطا در ارتباط با درگاه. لطفاً با پشتیبانی تماس بگیرید.'
        return render(request, 'store/payment_result.html', {'error': error_message})

# ==============================================================================
# VIEWS مربوط به پروفایل کاربران ثبت‌نامی
# ==============================================================================

@login_required(login_url='login')
def profile(request):
    # تغییر مهم: استفاده از filter و first به جای get
    # این کد می‌گوید: تمام مشتریانی که یوزرشان این است را بگیر، و اولی را به من بده.
    customer = Customer.objects.filter(user=request.user).first()

    # اگر مشتری اصلاً وجود نداشت، یکی بساز
    if not customer:
        customer = Customer.objects.create(
            user=request.user,
            name=request.user.username
        )

    orders = Order.objects.filter(customer=customer, complete=True).order_by('-date_ordered')
    context = {
        'orders': orders
    }
    return render(request, 'store/profile.html', context)

@login_required(login_url='login')
def order_detail(request, order_id):
    customer = Customer.objects.get(user=request.user)
    order = get_object_or_404(Order, id=order_id, customer=customer, complete=True)
    context = {
        'order': order,
        'order_items': order.orderitem_set.all(),
        'shipping_address': order.shippingaddress_set.first(),
    }
    return render(request, 'store/order_detail.html', context)