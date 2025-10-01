from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # آدرس برای نمایش لیست محصولات
    path('', views.product_list, name='product_list'),
    path('checkout/', views.checkout, name='checkout'),
    path('cart/', views.cart, name='cart'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    # آدرس برای نمایش جزئیات یک محصول
    # <slug:slug> یعنی یک متغیر به نام slug از نوع اسلاگ را از URL دریافت کن
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]