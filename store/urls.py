from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # آدرس برای نمایش لیست محصولات
    path('', views.product_list, name='product_list'),
    path('profile/', views.profile, name='profile'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'), # <-- این خط را اضافه کنید
    path('checkout/', views.checkout, name='checkout'),
    path('cart/', views.cart, name='cart'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('search/', views.search, name='search'),
    path('about/', views.about_page, name='about_page'),
    # آدرس برای نمایش جزئیات یک محصول
    # <slug:slug> یعنی یک متغیر به نام slug از نوع اسلاگ را از URL دریافت کن
    path('<slug:slug>/', views.product_detail, name='product_detail'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
   
]