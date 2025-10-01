from django.shortcuts import render, get_object_or_404
from .models import Category, Product
from .forms import CustomUserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from cart.cart import Cart
from .forms import ShippingForm
from .models import Order, OrderItem, ShippingAddress, Customer
from django.urls import reverse
from django.conf import settings
import requests


# Create your views here.

def product_list(request):
    products = Product.objects.filter(available=True)
    
    # --- بخش اشکال زدایی ---
    print("="*20)
    print(f"تعداد محصولات پیدا شده: {products.count()}")
    for p in products:
        print(f"- محصول: {p.name}, قیمت: {p.price}")
    print("="*20)
    # --- پایان بخش اشکال زدایی ---

    return render(request, 
                  'store/product/list.html', 
                  {'products': products})


    # product = Product.objects.filter(available=True)

    # return render(request, 'store/product/list.html', {'product': product})



def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)

    return render(request, 'store/product/detail.html', {'product': product})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # بعد از ثبت‌نام موفق، کاربر را به طور خودکار وارد سایت می‌کنیم
            login(request, user)
            return redirect('/') # کاربر به صفحه اصلی هدایت می‌شود
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required(login_url='login')
def checkout(request):
    cart = Cart(request)
    # اگر سبد خرید خالی بود، به صفحه اصلی برگرد
    if len(cart) == 0:
        return redirect('store:product_list')

    form = ShippingForm()
    if request.method == 'POST':
        form = ShippingForm(request.POST)
        if form.is_valid():
            # 1. گرفتن یا ساختن مشتری مرتبط با کاربر
            customer, created = Customer.objects.get_or_create(user=request.user)

            # 2. ساختن یک سفارش جدید در دیتابیس
            order = Order.objects.create(customer=customer, complete=False)

            # 3. انتقال آیتم‌ها از سبد خرید session به OrderItem های دیتابیس
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity']
                )

            # 4. ذخیره آدرس ارسال و اتصال آن به سفارش
            shipping_address = form.save(commit=False)
            shipping_address.customer = customer
            shipping_address.order = order
            shipping_address.save()

            # 5. پاک کردن سبد خرید session
            total_price_rial = int(cart.get_total_price() * 10)
            
            # آدرس بازگشت از درگاه پرداخت
            callback_url = request.build_absolute_uri(reverse('store:payment_verify'))

            # آماده‌سازی داده‌ها برای ارسال به آقای پرداخت
            pin_code = settings.MR_PARDDAKHT_API_KEY
            payment_data = {
                'pin': pin_code,
                'amount': total_price_rial,
                'callback': callback_url,
                'order_id': str(order.id),
                'description': f'سفارش شماره {order.id}',
        }
            
            # ارسال درخواست به آقای پرداخت
            # URL مربوط به درخواست پرداخت را از مستندات آقای پرداخت بردارید
            # این URL صرفا یک مثال است
            request_url = 'https://aqayepardakht.ir/api/v2/create'
            
            try:
              response = requests.post(request_url, json=payment_data)
              response.raise_for_status() # اگر کد وضعیت خطا بود، Exception ایجاد می‌کند
              response_json = response.json()

              if response_json.get('status') == 'success':
        # اگر درخواست موفق بود
        # آقای پرداخت authority را با نام 'transid' برمی‌گرداند
                authority = response_json.get('transid')
                payment_url = f"https://aqayepardakht.ir/startpay/{authority}"

                # ذخیره کد رهگیری (authority/transid) در سفارش
                order.transaction_id = authority
                order.save()

                # پاک کردن سبد خرید session
                cart.clear()
                
                # هدایت کاربر به صفحه پرداخت
                return redirect(payment_url)
              else:
                # اگر وضعیت success نبود
                error_message = response_json.get('message', 'خطا در ایجاد تراکنش.')
                # برگرداندن کاربر به صفحه سبد خرید با پیام خطا
                # (باید راهی برای نمایش این خطا در قالب cart/detail.html داشته باشید)
                return render(request, 'cart/detail.html', {'error': error_message})
            except requests.exceptions.RequestException as e:
                # اگر خطایی در ارتباط شبکه رخ داد (مثل SSLError قبلی)
                # می‌توانید این خطا را لاگ کنید و یک پیام عمومی به کاربر نشان دهید
                print(f"Error connecting to payment gateway: {e}")
                error_message = 'خطا در اتصال به درگاه پرداخت. لطفاً لحظاتی دیگر تلاش کنید.'
                return render(request, 'cart/detail.html', {'error': error_message})
            
    else: # اگر متد GET بود
        form = ShippingForm()

    context = {'form': form, 'cart': cart}
    return render(request, 'store/checkout.html', context)

def cart(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})


def payment_verify(request):
    # آقای پرداخت transid را از طریق GET ارسال می‌کند
    transid = request.GET.get('transid')

    if not transid:
        return render(request, 'store/payment_result.html', {'error': 'اطلاعات بازگشتی از درگاه ناقص است.'})

    try:
        # ما transid را به عنوان transaction_id ذخیره کرده بودیم
        order = Order.objects.get(transaction_id=transid)
    except Order.DoesNotExist:
        return render(request, 'store/payment_result.html', {'error': 'سفارش یافت نشد.'})

    # مبلغ سفارش به ریال
    amount_rial = int(order.get_cart_total() * 10)
    pin_code = settings.MR_PARDDAKHT_API_KEY
    
    verify_data = {
        'pin': pin_code,
        'amount': amount_rial,
        'transid': transid
    }

    # آدرس API برای تأیید تراکنش (مطابق مستندات)
    verify_url = 'https://aqayepardakht.ir/api/v2/verify'
    
    try:
        response = requests.post(verify_url, json=verify_data)
        response.raise_for_status()
        response_json = response.json()

        if response_json.get('status') == 'success':
            # پرداخت با موفقیت تأیید شد
            order.complete = True
            order.save()
            # می‌توانید شماره کارت پرداخت شده را هم ذخیره کنید:
            # card_number = response_json.get('card_number')
            return render(request, 'store/payment_result.html', {'order': order, 'success': True})
        else:
            # تأیید پرداخت ناموفق بود
            error_message = response_json.get('message', 'تراکنش توسط درگاه تأیید نشد.')
            return render(request, 'store/payment_result.html', {'order': order, 'error': error_message})

    except requests.exceptions.RequestException as e:
        print(f"Error verifying payment: {e}")
        error_message = 'خطا در ارتباط با درگاه برای تأیید تراکنش.'
        return render(request, 'store/payment_result.html', {'order': order, 'error': error_message})