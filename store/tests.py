from django.test import TestCase
from django.conf import settings

# store/tests.py

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Customer, Order, Product, Category

class SecurityTests(TestCase):

    def setUp(self):
        """
        این متد قبل از اجرای هر تست اجرا می‌شود و داده‌های اولیه را می‌سازد.
        """
        # --- ایجاد کاربران و مشتریان ---
        # کاربر اول که مالک داده‌ها خواهد بود
        self.user1 = User.objects.create_user(username='user1', password='password123', email='user1@test.com')
        self.customer1 = Customer.objects.create(user=self.user1, name='User One')

        # کاربر دوم که به عنوان مهاجم فرضی عمل می‌کند
        self.user2 = User.objects.create_user(username='user2', password='password123', email='user2@test.com')
        self.customer2 = Customer.objects.create(user=self.user2, name='User Two')

        # --- ایجاد داده‌های مرتبط ---
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            category=self.category,
            name='Test Product',
            slug='test-product',
            price=100.00,
            stock=10
        )
        
        # یک سفارش کامل شده برای کاربر اول
        self.order_for_user1 = Order.objects.create(customer=self.customer1, complete=True)

        # ایجاد یک کلاینت تست برای شبیه‌سازی درخواست‌های مرورگر
        self.client = Client()

    # ====== تست‌های مربوط به صفحه جزئیات سفارش (order_detail) ======

    def test_order_owner_can_access_order_detail(self):
        """
        تست موفق: مالک سفارش باید بتواند جزئیات سفارش خود را ببیند (Status Code 200).
        """
        # با کاربر اول (مالک سفارش) وارد می‌شویم
        self.client.login(username='user1', password='password123')
        
        url = reverse('store:order_detail', args=[self.order_for_user1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"جزئیات سفارش شماره #{self.order_for_user1.id}")

    def test_other_user_cannot_access_order_detail(self):
        """
        تست امنیتی: کاربر دیگر نباید بتواند به جزئیات سفارش دسترسی پیدا کند (Status Code 404).
        """
        # با کاربر دوم (غیر مالک) وارد می‌شویم
        self.client.login(username='user2', password='password123')
        
        url = reverse('store:order_detail', args=[self.order_for_user1.id])
        response = self.client.get(url)
        
        # انتظار داریم با خطای 404 (Not Found) مواجه شویم، چون منطق شما اینطور پیاده‌سازی شده
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_from_order_detail(self):
        """
        تست امنیتی: کاربر وارد نشده (ناشناس) باید به صفحه لاگین هدایت شود (Status Code 302).
        """
        # بدون لاگین درخواست می‌دهیم
        url = reverse('store:order_detail', args=[self.order_for_user1.id])
        response = self.client.get(url)
        
        login_url = reverse('login')
        # بررسی می‌کنیم که آیا به صفحه لاگین با پارامتر next صحیح ریدایرکت شده است
        self.assertRedirects(response, f'{login_url}?next={url}')

    # ====== تست‌های مربوط به صفحه پروفایل (profile) ======

    def test_logged_in_user_can_access_profile(self):
        """
        تست موفق: کاربر وارد شده باید بتواند به صفحه پروفایل خود دسترسی پیدا کند (Status Code 200).
        """
        self.client.login(username='user1', password='password123')
        url = reverse('store:profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "تاریخچه سفارشات شما")

    def test_anonymous_user_is_redirected_from_profile(self):
        """
        تست امنیتی: کاربر ناشناس باید از صفحه پروفایل به صفحه لاگین هدایت شود (Status Code 302).
        """
        url = reverse('store:profile')
        response = self.client.get(url)

        login_url = reverse('login')
        self.assertRedirects(response, f'{login_url}?next={url}')

    # ====== تست‌های مربوط به صفحه تسویه حساب (checkout) ======

    def test_logged_in_user_can_access_checkout_with_items_in_cart(self):
        """
        تست موفق: کاربر وارد شده با سبد خرید پر باید بتواند صفحه تسویه حساب را ببیند (Status Code 200).
        """
        session = self.client.session
        session[settings.CART_SESSION_ID] = {
            str(self.product.id): {'quantity': 1, 'price': str(self.product.price)}
        }
        session.save()

        self.client.login(username='user1', password='password123')
        url = reverse('store:checkout')
        response = self.client.get(url)

        # ========== خط تشخیصی را اینجا اضافه کنید ==========
        # print(response.content.decode('utf-8'))
        # ===============================================

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "اطلاعات ارسال")

    def test_anonymous_user_is_redirected_from_checkout(self):
        """
        تست امنیتی: کاربر ناشناس باید از صفحه تسویه حساب به صفحه لاگین هدایت شود (Status Code 302).
        """
        url = reverse('store:checkout')
        response = self.client.get(url)

        login_url = reverse('login')
        self.assertRedirects(response, f'{login_url}?next={url}')

    def test_logged_in_user_is_redirected_from_checkout_if_cart_is_empty(self):
        """
        تست منطقی: کاربر وارد شده با سبد خرید خالی باید به لیست محصولات هدایت شود (Status Code 302).
        """
        self.client.login(username='user1', password='password123')
        url = reverse('store:checkout')
        response = self.client.get(url)
        
        # بر اساس منطق ویوی شما، باید به صفحه لیست محصولات ریدایرکت شود
        product_list_url = reverse('store:product_list')
        self.assertRedirects(response, product_list_url)
