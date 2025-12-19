

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
from .models import Category, Product, Order, OrderItem, ShippingAddress, Customer, Brand
from .forms import CustomUserCreationForm, ShippingForm
from cart.cart import Cart
from .utils_payment import debug_prepare_payment_data, debug_handle_response
from django.contrib.auth import login
from .utils_shipping import calculate_shipping_cost
import logging
import secrets
from .forms import UsernameRecoveryForm, SecurityAnswerForm, PasswordResetForm, ReviewForm, ProductFilterForm
from .telegram_utils import send_bale_order_notification
from django.utils import timezone
from .models import Coupon, Review, Wishlist, Category, Product, Brand
from django.db.models import Avg # برای محاسبه میانگین امتیاز
from django.db.models import Count, Q, Case, When, Value, IntegerField

logger = logging.getLogger(__name__)

# ==============================================================================
# VIEWS مربوط به نمایش محصولات و صفحات عمومی
# ==============================================================================

def product_list(request, category_slug=None):
    category = None
    products_all = Product.objects.filter(available=True)
    
    # فیلتر بر اساس دسته‌بندی (URL)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products_all = products_all.filter(category=category)

    # --- بخش جدید: اعمال فیلترهای فرم ---
    filter_form = ProductFilterForm(request.GET)
    
    if filter_form.is_valid():
        # 1. فیلتر قیمت
        min_p = filter_form.cleaned_data.get('min_price')
        max_p = filter_form.cleaned_data.get('max_price')
        if min_p:
            products_all = products_all.filter(price__gte=min_p)
        if max_p:
            products_all = products_all.filter(price__lte=max_p)
            
        # 2. فیلتر موجودی
        if filter_form.cleaned_data.get('in_stock'):
            products_all = products_all.filter(stock__gt=0)
            
        # 3. فیلتر برند
        brands = filter_form.cleaned_data.get('brands')
        if brands:
            products_all = products_all.filter(brand__in=brands)
    # -------------------------------------

    # بخش‌های قبلی (پرفروش و تخفیف‌دار) - این‌ها را معمولاً فیلتر نمی‌کنیم
    # اما اگر بخواهید فیلتر روی این‌ها هم اعمال شود، باید کدهای فیلتر را بالاتر ببرید.
    # در اینجا فرض بر این است فیلتر فقط روی لیست اصلی پایین صفحه اعمال می‌شود.
    bestsellers = Product.objects.filter(available=True, is_bestseller=True)[:4]
    discounted = Product.objects.filter(available=True, old_price__isnull=False).exclude(old_price=0)[:4]
    
    # صفحه‌بندی (روی محصولات فیلتر شده)
    paginator = Paginator(products_all, 12) 
    page_number = request.GET.get('page')
    products_paginated = paginator.get_page(page_number)
    
    # برای نگه داشتن فیلترها هنگام عوض کردن صفحه (Pagination)
    # یک رشته کوئری می‌سازیم (مثلا &min_price=100&brands=1)
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    url_params = query_params.urlencode()

    context = {
        'category': category, 
        'products': products_paginated,
        'bestsellers': bestsellers, 
        'discounted': discounted,
        'filter_form': filter_form, # ارسال فرم به قالب
        'url_params': url_params,   # ارسال پارامترهای URL برای صفحه‌بندی
    }
    return render(request, 'store/product/list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    
    # ------------------------------------------------------------------
    # 👇👇👇 منطق هوشمند محصولات مرتبط (Smart Related Products) 👇👇👇
    # ------------------------------------------------------------------
    
    # 1. دریافت لیست مقادیر ویژگی‌های محصول فعلی (مثلاً: قرمز، XL، کتان)
    current_attr_values = product.attributes.values_list('value', flat=True)

    related_products = Product.objects.filter(
        category=product.category,  # شرط ۱: حتماً هم‌دسته باشند
        available=True
    ).exclude(
        id=product.id  # خود محصول فعلی را حذف کن
    ).annotate(
        # امتیازدهی ۱: آیا برند یکسان است؟ (اگر بله ۱ امتیاز، اگر نه ۰)
        is_same_brand=Case(
            When(brand=product.brand, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        ),
        # امتیازدهی ۲: تعداد ویژگی‌های مشترک را بشمار
        # (هرچقدر ویژگی‌های مثل رنگ یا سایز مشابه بیشتر باشد، عدد بزرگتر می‌شود)
        shared_tags_count=Count(
            'attributes', 
            filter=Q(attributes__value__in=current_attr_values)
        )
    ).order_by(
        '-is_same_brand',       # اولویت اول: هم‌برندها بالاتر
        '-shared_tags_count',   # اولویت دوم: بیشترین شباهت ویژگی
        '-created'              # اولویت سوم: جدیدترین‌ها
    )[:4] # فقط ۴ تا را برگردان
    
    # ------------------------------------------------------------------

    # کدهای قبلی (نظرات و لیست علاقه‌مندی) بدون تغییر باقی می‌مانند
    reviews = Review.objects.filter(product=product, status=True)
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    is_in_wishlist = False
    if request.user.is_authenticated:
        if Wishlist.objects.filter(user=request.user, products=product).exists():
            is_in_wishlist = True

    context = {
        'product': product, 
        'related_products': related_products, # حالا لیست هوشمند ارسال می‌شود
        'reviews': reviews,
        'average_rating': average_rating,
        'review_form': ReviewForm(),
        'is_in_wishlist': is_in_wishlist,
    }
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
# VIEWS مربوط به ثبت نام سنتی
# ==============================================================================

def register(request):
    if request.user.is_authenticated:
        return redirect('store:product_list')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            phone = form.cleaned_data.get('phone_number')
            question = form.cleaned_data.get('security_question')
            raw_answer = form.cleaned_data.get('security_answer')

            customer, created = Customer.objects.get_or_create(
                user=user,
                defaults={
                    'name': user.username,
                    'phone_number': phone,
                    'security_question': question
                }
            )

            if raw_answer:
                customer.set_security_answer(raw_answer)
                customer.save()

            if not created:
                customer.phone_number = phone
                customer.security_question = question
                customer.set_security_answer(raw_answer)
                customer.save()

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('/')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

# ==============================================================================
# VIEWS مربوط به فرآیند OTP
# ==============================================================================

def otp_page(request):
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

        otp = str(secrets.randbelow(899999) + 100000)

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
        phone = request.POST.get("phone") or request.session.get('pending_phone')
        code = request.POST.get("code")

        if not phone or not code:
            return JsonResponse({"success": False, "message": "اطلاعات ناقص است."}, status=400)

        saved_code = cache.get(f"otp_{phone}")
        
        # بررسی صحت کد OTP
        if saved_code and str(saved_code) == str(code):
            cache.delete(f"otp_{phone}")
            
            cart = request.cart
            shipping_data = request.session.get('shipping_data')
            
            if not shipping_data or len(cart) == 0:
                return JsonResponse({
                    "success": False, 
                    "message": "اطلاعات سبد خرید یا آدرس یافت نشد. لطفاً مجدد تلاش کنید.",
                    "redirect_url": reverse('store:checkout')
                })

            try:
                full_name = shipping_data.get('full_name', f"کاربر {phone}")
                
                # ==========================================================
                # بخش ۱: همگام‌سازی کاربر (User Sync Logic) ✅
                # ==========================================================
                customer = None
                
                if request.user.is_authenticated:
                    # اولویت با کاربر لاگین شده است
                    customer = Customer.objects.filter(user=request.user).first()
                    
                    if customer:
                        # اگر کاربر پروفایل دارد و شماره جدیدی وریفای کرده، آپدیت کن (اگر تکراری نباشد)
                        if customer.phone_number != phone:
                            if not Customer.objects.filter(phone_number=phone).exclude(id=customer.id).exists():
                                customer.phone_number = phone
                                customer.save()
                        
                        # اگر نام نداشت، نام فرم را ست کن
                        if not customer.name:
                            customer.name = full_name
                            customer.save()
                            
                    else:
                        # کاربر لاگین است اما پروفایل ندارد (شاید قبلا به صورت مهمان با این شماره خرید کرده)
                        existing_guest = Customer.objects.filter(phone_number=phone, user__isnull=True).first()
                        
                        if existing_guest:
                            # اتصال اکانت مهمان به اکانت کاربری
                            customer = existing_guest
                            customer.user = request.user
                            customer.name = full_name
                            customer.save()
                        else:
                            # ساخت مشتری جدید متصل به یوزر
                            customer = Customer.objects.create(
                                user=request.user,
                                phone_number=phone,
                                name=full_name
                            )
                else:
                    # کاربر مهمان است
                    customer, created = Customer.objects.get_or_create(
                        phone_number=phone,
                        defaults={'name': full_name}
                    )
                    if not created and not customer.name:
                        customer.name = full_name
                        customer.save()
                # ==========================================================

                # بخش ۲: محاسبات مالی و هزینه ارسال
                shipping_method = shipping_data.get('shipping_method', 'mahex')
                total_weight = cart.get_total_weight()
                
                # دریافت مبلغ کل سبد خرید (اگر متد get_total_price را آپدیت کرده باشید، تخفیف لحاظ شده است)
                cart_total_price = cart.get_total_price()
                
                final_shipping_cost = 0
                if shipping_method == 'post':
                    final_shipping_cost = calculate_shipping_cost(total_weight)
                
                final_total_price = float(cart_total_price) + float(final_shipping_cost)

                # بخش ۳: ایجاد سفارش در دیتابیس
                order = Order.objects.create(
                    customer=customer, 
                    complete=False, 
                    total_price=final_total_price,
                    shipping_method=shipping_method,
                    shipping_cost=final_shipping_cost,
                    status='pending'
                )

                # ثبت آیتم‌های سفارش
                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        quantity=item['quantity'],
                        price=item['price']
                    )

                # ثبت آدرس ارسال
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

                # بخش ۴: اتصال به درگاه پرداخت
                amount_toman = int(final_total_price)
                callback_url = request.build_absolute_uri(reverse('store:payment_verify'))
                
                payment_data = {
                    'pin': settings.MR_PARDDAKHT_API_KEY,
                    'amount': amount_toman,
                    'callback': callback_url,
                    'order_id': str(order.id),
                    'description': f'پرداخت سفارش شماره {order.id} | موبایل: {phone}',
                    'mobile': phone,
                }

                debug_prepare_payment_data(payment_data)

                request_url = 'https://panel.aqayepardakht.ir/api/v2/create'
                headers = {'Content-Type': 'application/json'}

                response = requests.post(request_url, json=payment_data, headers=headers, timeout=10)
                response.raise_for_status()
                response_json = response.json()
                
                debug_handle_response(response_json)

                if response_json.get('status') == 'success':
                    transid = response_json.get('transid')
                    order.transaction_id = transid
                    order.save()
                    
                    # پاک کردن اطلاعات موقت سشن
                    del request.session['shipping_data']
                    
                    # ✅ اگر سیستم کد تخفیف را پیاده کرده‌اید، این خط را اضافه کنید:
                    request.session['coupon_id'] = None 
                    
                    payment_url = f"https://panel.aqayepardakht.ir/startpay/{transid}"
                    return JsonResponse({
                        "success": True, 
                        "message": "در حال انتقال به درگاه پرداخت...",
                        "redirect_url": payment_url
                    })
                else:
                    # در صورت خطای درگاه، سفارش را کنسل می‌کنیم (حذف نمی‌کنیم)
                    order.status = 'cancelled'
                    order.save()
                    
                    logger.error(f"Payment creation failed: {response_json}")
                    return JsonResponse({
                        "success": False, 
                        "message": f"خطا در درگاه پرداخت: {response_json.get('message', 'خطای ناشناخته')}"
                    })

            except Exception as e:
                # مدیریت خطاهای غیرمنتظره
                if 'order' in locals() and order.id:
                    order.status = 'cancelled'
                    order.save()
                
                logger.exception("Error processing verify_otp order creation")
                return JsonResponse({
                    "success": False, 
                    "message": "خطا در ثبت سفارش. لطفاً دقایقی دیگر تلاش کنید."
                })

        else:
            return JsonResponse({"success": False, "message": "کد وارد شده نادرست یا منقضی شده است."})
    
    return JsonResponse({"error": "درخواست نامعتبر."}, status=405)

# ==============================================================================
# VIEWS مربوط به فرآیند خرید و پرداخت
# ==============================================================================

def checkout(request):
    cart = request.cart
    if len(cart) == 0:
        return redirect('store:product_list')

    total_weight = cart.get_total_weight()
    shipping_cost_post = calculate_shipping_cost(total_weight)

    if request.method == 'POST':
        form = ShippingForm(request.POST)
        if form.is_valid():
            shipping_data = form.cleaned_data
            phone_number = shipping_data.get('phone_number')
            selected_method = request.POST.get('shipping_method')
            
            request.session['shipping_data'] = shipping_data
            request.session['shipping_data']['shipping_method'] = selected_method
            request.session['pending_phone'] = phone_number
            
            return redirect('store:otp_page')
    else:
        saved_data = request.session.get('shipping_data')
        form = ShippingForm(initial=saved_data) if saved_data else ShippingForm()

    context = {
        'form': form, 
        'cart': cart,
        'shipping_cost_post': shipping_cost_post,
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
        # فقط سفارش‌هایی که هنوز تکمیل نشده‌اند را بگیر
        order = Order.objects.get(transaction_id=transid, complete=False)
    except Order.DoesNotExist:
        # اگر سفارش قبلاً تکمیل شده باشد
        if Order.objects.filter(transaction_id=transid, complete=True).exists():
            order_done = Order.objects.get(transaction_id=transid)
            return render(request, 'store/payment_result.html', {'order': order_done, 'success': True, 'already_verified': True})
        logger.error(f"Order with transid {transid} not found") 
        return render(request, 'store/payment_result.html', {'error': 'سفارش یافت نشد.'})

    # محاسبه مبلغ مورد انتظار به ریال
    # نکته: بهتر است از int روی Decimal استفاده کنید تا دقت حفظ شود، اما طبق کد قبلی شما float هم کار می‌کند
    expected_amount_rials = int(order.total_price * 10)

    # آماده‌سازی داده‌ها برای تایید نهایی
    verify_data = {
        'pin': settings.MR_PARDDAKHT_API_KEY, 
        'amount': expected_amount_rials, 
        'transid': transid
    }

    debug_prepare_payment_data(verify_data)

    verify_url = 'https://panel.aqayepardakht.ir/api/v2/verify'
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(verify_url, json=verify_data, headers=headers, timeout=10)
        response.raise_for_status()
        response_json = response.json()

        logger.info(f"Payment verify response: {response_json}")
        
        if response_json.get('status') == 'success':
            # ==================================================================
            # اصلاحیه امنیتی: بررسی تطابق مبلغ (Amount Validation) 🛡️
            # ==================================================================
            # درگاه معمولاً مبلغ تایید شده را در پاسخ برمی‌گرداند.
            # اگر کلید amount در پاسخ نبود، همان مبلغ ارسالی را فرض می‌گیریم (بسته به مستندات درگاه)
            paid_amount = int(response_json.get('amount', expected_amount_rials))
            
            if paid_amount != expected_amount_rials:
                # اگر مبلغ پرداخت شده کمتر یا بیشتر از مبلغ سفارش بود
                logger.critical(f"Payment Fraud Attempt! Order: {order.id}, Expected: {expected_amount_rials}, Paid: {paid_amount}")
                
                order.status = 'cancelled' # یا یک وضعیت خاص مثل 'fraud_check'
                order.save()
                
                return render(request, 'store/payment_result.html', {
                    'error': 'مبلغ پرداخت شده با مبلغ سفارش مغایرت دارد. تراکنش لغو شد.'
                })
            # ==================================================================

            # --- پرداخت و مبلغ تایید شد ---
            order.complete = True
            order.status = 'paid'
            
            # کسر موجودی انبار (از اصلاحات قبلی)
            for item in order.orderitem_set.all():
                product = item.product
                if product.stock >= item.quantity:
                    product.stock -= item.quantity
                    product.save()
                else:
                    logger.warning(f"Order {order.id}: Product {product.id} stock was {product.stock}, needed {item.quantity}. Set to 0.")
                    product.stock = 0
                    product.save()

            order.save()

            try:
                send_bale_order_notification(order)
            except Exception as e:
                logger.error(f"Failed to send telegram notification: {e}")
            
            # پاک‌سازی
            request.cart.clear()
            request.session.pop('phone_verified', None)
            request.session.pop('next_url', None)
            
            return render(request, 'store/payment_result.html', {'order': order, 'success': True})
        else:
            # پرداخت ناموفق
            error_message = response_json.get('message', 'تراکنش توسط درگاه تأیید نشد.')
            logger.error(f"Payment verification failed: {response_json}")
            
            # تغییر وضعیت به جای حذف (از اصلاحات قبلی)
            order.status = 'cancelled'
            order.save()
            
            return render(request, 'store/payment_result.html', {'error': error_message})
            
    except requests.exceptions.RequestException as e:
        logger.exception("Error verifying payment with gateway")
        error_message = 'خطا در ارتباط با درگاه. لطفاً با پشتیبانی تماس بگیرید.'
        return render(request, 'store/payment_result.html', {'error': error_message})

# ==============================================================================
# VIEWS مربوط به پروفایل کاربران
# ==============================================================================

@login_required(login_url='login')
def profile(request):
    customer = Customer.objects.filter(user=request.user).first()

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

def forgot_password_request(request):
    """مرحله ۱: دریافت نام کاربری برای پیدا کردن سوال"""
    if request.method == 'POST':
        form = UsernameRecoveryForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['identifier']
            # جستجو بر اساس نام کاربری یا موبایل
            customer = Customer.objects.filter(
                Q(user__username=identifier) | Q(phone_number=identifier)
            ).first()

            if customer and customer.security_question and customer.security_answer:
                # ذخیره ID مشتری در سشن برای مرحله بعد
                request.session['reset_customer_id'] = customer.id
                return redirect('store:verify_security_question')
            else:
                messages.error(request, "کاربری با این مشخصات یافت نشد یا سوال امنیتی تنظیم نکرده است.")
    else:
        form = UsernameRecoveryForm()
    
    return render(request, 'registration/forgot_password.html', {'form': form})

def verify_security_question(request):
    """مرحله ۲: نمایش سوال و بررسی پاسخ"""
    customer_id = request.session.get('reset_customer_id')
    if not customer_id:
        return redirect('store:forgot_password')
    
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == 'POST':
        form = SecurityAnswerForm(request.POST)
        if form.is_valid():
            answer = form.cleaned_data['answer']
            if customer.check_security_answer(answer):
                # پاسخ صحیح است، اجازه ورود به مرحله تغییر رمز
                request.session['security_verified'] = True
                return redirect('store:reset_password_confirm')
            else:
                messages.error(request, "پاسخ اشتباه است.")
    else:
        form = SecurityAnswerForm()

    return render(request, 'registration/security_question.html', {
        'form': form,
        'question': customer.security_question
    })

def reset_password_confirm(request):
    """مرحله ۳: تغییر رمز عبور"""
    customer_id = request.session.get('reset_customer_id')
    is_verified = request.session.get('security_verified')

    if not customer_id or not is_verified:
        return redirect('store:forgot_password')
    
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            new_pass = form.cleaned_data['new_password']
            user = customer.user
            if user:
                user.set_password(new_pass)
                user.save()
                
                # پاک کردن سشن‌های موقت
                del request.session['reset_customer_id']
                del request.session['security_verified']
                
                messages.success(request, "رمز عبور با موفقیت تغییر کرد. اکنون وارد شوید.")
                return redirect('login')
            else:
                messages.error(request, "خطایی در کاربر متصل رخ داده است.")
    else:
        form = PasswordResetForm()

    return render(request, 'registration/reset_password.html', {'form': form})


def coupon_apply(request):
    now = timezone.now()
    code = request.POST.get('code')
    try:
        coupon = Coupon.objects.get(code__iexact=code,
                                    valid_from__lte=now,
                                    valid_to__gte=now,
                                    active=True)
        request.session['coupon_id'] = coupon.id
        messages.success(request, 'کد تخفیف با موفقیت اعمال شد.')
    except Coupon.DoesNotExist:
        request.session['coupon_id'] = None
        messages.error(request, 'کد تخفیف معتبر نیست.')
    
    return redirect('cart:cart_detail')



def submit_review(request, product_id):
    if request.method == 'POST':
        try:
            # بررسی لاگین بودن کاربر
            if not request.user.is_authenticated:
                messages.error(request, "برای ثبت نظر ابتدا باید وارد حساب کاربری خود شوید.")
                return redirect('login')

            product = get_object_or_404(Product, id=product_id)
            
            # بررسی اینکه آیا کاربر قبلا نظر داده یا نه (اختیاری)
            # اگر می‌خواهید هر کاربر فقط یک نظر بدهد، کامنت زیر را فعال کنید:
            # if Review.objects.filter(user=request.user, product=product).exists():
            # messages.warning(request, "شما قبلاً برای این محصول نظر ثبت کرده‌اید.")
            #     return redirect(product.get_absolute_url())

            form = ReviewForm(request.POST)
            if form.is_valid():
                data = form.save(commit=False)
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.comment = form.cleaned_data['comment']
                data.product = product
                data.user = request.user
                data.save()
                messages.success(request, "نظر شما با موفقیت ثبت شد و پس از تایید مدیریت نمایش داده می‌شود.")
                return redirect(product.get_absolute_url())
            else:
                messages.error(request, "اطلاعات فرم صحیح نیست.")
                return redirect(product.get_absolute_url())
                
        except Exception as e:
            messages.error(request, f"خطا در ثبت نظر: {e}")
            return redirect('store:product_list')
            
    return redirect('store:product_list')



@login_required(login_url='login')
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # دریافت یا ایجاد لیست برای کاربر
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if product in wishlist.products.all():
        # اگر محصول در لیست بود، حذفش کن
        wishlist.products.remove(product)
        messages.info(request, f"{product.name} از لیست علاقه‌مندی‌ها حذف شد.")
    else:
        # اگر نبود، اضافه‌اش کن
        wishlist.products.add(product)
        messages.success(request, f"{product.name} به لیست علاقه‌مندی‌ها اضافه شد.")
    
    # بازگشت به همان صفحه‌ای که کاربر در آن بوده (مثلا صفحه محصول)
    return redirect(request.META.get('HTTP_REFERER', 'store:product_list'))

@login_required(login_url='login')
def wishlist_page(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    products = wishlist.products.all()
    return render(request, 'store/wishlist.html', {'products': products})


