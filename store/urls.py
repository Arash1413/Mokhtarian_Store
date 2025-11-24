# from django.urls import path
# from . import views

# app_name = 'store'

# urlpatterns = [
#     # آدرس برای نمایش لیست محصولات
#     path('', views.product_list, name='product_list'),
#     path('profile/', views.profile, name='profile'),
#     path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'), # <-- این خط را اضافه کنید
#     path('checkout/', views.checkout, name='checkout'),
#     path('cart/', views.cart, name='cart'),
#     path('payment/verify/', views.payment_verify, name='payment_verify'),
#     path('search/', views.search, name='search'),
#     path('about/', views.about_page, name='about_page'),
#     # آدرس برای نمایش جزئیات یک محصول
#     # <slug:slug> یعنی یک متغیر به نام slug از نوع اسلاگ را از URL دریافت کن
#     path('<slug:slug>/', views.product_detail, name='product_detail'),
#     path('order/<int:order_id>/', views.order_detail, name='order_detail'),
#     path('otp/send/', views.send_otp, name='send_otp'),
#     path('otp/verify/', views.verify_otp, name='otp_verify'),
#     path('otp/', views.otp_page, name='otp_page'),
#     path('checkout/', views.checkout, name='checkout'),
   
# ]
# store/urls.py (ترتیب صحیح)

from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # آدرس‌های عمومی و استاتیک در ابتدا
    path('', views.product_list, name='product_list'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('search/', views.search, name='search'),
    path('about/', views.about_page, name='about_page'),
    path('register/', views.register, name='register'), # اگر هنوز از آن استفاده می‌کنید
    
    # آدرس‌های مربوط به پروفایل
    path('profile/', views.profile, name='profile'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),

    # آدرس‌های مربوط به OTP (قبل از الگوی کلی slug)
    path('otp/', views.otp_page, name='otp_page'),
    path('otp/send/', views.send_otp, name='send_otp'),
    path('otp/verify/', views.verify_otp, name='verify_otp'),

    # آدرس‌های مربوط به پرداخت
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    
    # آدرس‌های داینامیک در انتها
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    
    # الگوی کلی slug باید آخرین الگو باشد
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]