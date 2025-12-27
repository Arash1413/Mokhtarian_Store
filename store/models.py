from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from simple_history.models import HistoricalRecords
from django.contrib.auth.hashers import make_password
from django.core.validators import MinValueValidator, MaxValueValidator



# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True)

    seo_title = models.CharField(max_length=200, blank=True, verbose_name="عنوان سئو (Title)")
    seo_description = models.TextField(blank=True, verbose_name="توضیحات سئو (Meta Description)")

    # رفتار مدل
    class Meta:
        ordering = ('name',)
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
            return self.name
    
class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
        
class Product(models.Model):
    wholesale_min_qty = models.PositiveIntegerField(default=0, help_text="حداقل تعداد برای اعمال قیمت عمده (0 یعنی غیرفعال)")
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, help_text="قیمت محصول در صورت خرید عمده")
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, related_name='products', on_delete=models.CASCADE, null=True, blank=True) # <-- فیلد جدید # 
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, db_index=True)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # <-- فیلد جدید
    is_bestseller = models.BooleanField(default=False) # <-- فیلد جدید
    weight = models.PositiveIntegerField(default=0, help_text="وزن محصول به گرم")
    min_order_quantity = models.PositiveIntegerField(default=1, verbose_name="حداقل تعداد سفارش")
    max_order_quantity = models.PositiveIntegerField(null=True, blank=True, verbose_name="حداکثر تعداد سفارش (خالی = نامحدود)")

    seo_title = models.CharField(max_length=200, blank=True, verbose_name="عنوان سئو (Title)")
    seo_description = models.TextField(blank=True, verbose_name="توضیحات سئو (Meta Description)")

    class Meta:
        ordering = ('-created',)
        indexes = [
            models.Index(fields=['id', 'slug']),
        ]

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])
    
    def get_current_price(self, quantity):
        """
        این متد قیمت را بر اساس تعداد ورودی محاسبه می‌کند
        """
        if self.wholesale_min_qty > 0 and self.wholesale_price and quantity >= self.wholesale_min_qty:
            return self.wholesale_price
        return self.price

    def __str__(self):
        return self.name
    



class Customer(models.Model):
    security_question = models.CharField(max_length=255, blank=True, null=True, help_text="سوال امنیتی که کاربر طرح کرده است")
    security_answer = models.CharField(max_length=255, blank=True, null=True, help_text="پاسخ هش شده سوال امنیتی")
    
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    

    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True) # اضافه کردن unique=True

    def set_security_answer(self, raw_answer):
        from django.contrib.auth.hashers import make_password
        """پاسخ را نرمال‌سازی و هش می‌کند"""
        if raw_answer:
            
            clean_answer = raw_answer.strip().lower()
            self.security_answer = make_password(clean_answer)
    
    def check_security_answer(self, raw_answer):
        """بررسی صحت پاسخ وارد شده"""
        from django.contrib.auth.hashers import check_password
        if raw_answer:
            clean_answer = raw_answer.strip().lower()
            return check_password(clean_answer, self.security_answer)
        return False

    def __str__(self):
        
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.phone_number or f"Customer {self.id}"
    

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'ثبت شده / در صف بررسی'),
        ('processing', 'در حال آماده‌سازی'),
        ('shipped', 'تحویل پست شده'),
        ('delivered', 'تحویل مشتری شده'),
        ('cancelled', 'لغو شده'),
    ]

    SHIPPING_CHOICES = [
        ('mahex', 'ماهکس (پس‌کرایه)'),
        ('post', 'پست پیشتاز'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=200, null=True)
    shipping_method = models.CharField(max_length=20, null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت سفارش')
    tracking_code = models.CharField(max_length=50, null=True, blank=True, verbose_name='کد رهگیری پستی')
    

    history = HistoricalRecords()

    def __str__(self):
        return str(self.id)
    
    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total
    
    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total 
    

class OrderItem(models.Model):
    
    product = models.ForeignKey(Product, on_delete=models.PROTECT) 
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    
    quantity = models.PositiveIntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=0, default=0) 

    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total
    

class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    full_name = models.CharField(max_length=200, null=True)  
    phone_number = models.CharField(max_length=20, null=True) 
    address = models.CharField(max_length=200, null=False)
    city = models.CharField(max_length=200, null=False)
    state = models.CharField(max_length=200, null=False) 
    zipcode = models.CharField(max_length=200, null=False) 
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address
    
class Attribute(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, related_name='attributes', on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: {self.value}"
    




class FAQ(models.Model):
    question = models.CharField(max_length=255, verbose_name="سوال")
    answer = models.TextField(verbose_name="پاسخ")
    sort_order = models.IntegerField(default=0, verbose_name="ترتیب نمایش")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        ordering = ['sort_order']
        verbose_name = "سوال متداول"
        verbose_name_plural = "سوالات متداول"

    def __str__(self):
        return self.question
    


from django.core.validators import MinValueValidator, MaxValueValidator

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="کد تخفیف")
    valid_from = models.DateTimeField(verbose_name="معتبر از")
    products = models.ManyToManyField('Product', blank=True, verbose_name="محصولات مجاز")
    valid_to = models.DateTimeField(verbose_name="معتبر تا")
    discount = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="درصد تخفیف"
    )
    active = models.BooleanField(default=True, verbose_name="فعال")

    def __str__(self):
        return self.code
    


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="محصول")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    subject = models.CharField(max_length=100, blank=True, verbose_name="عنوان")
    comment = models.TextField(max_length=500, verbose_name="متن نظر")
    rating = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="امتیاز")
    status = models.BooleanField(default=False, verbose_name="وضعیت تایید") # فقط با تایید مدیر نمایش داده شود
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} - {self.user.username}"

    class Meta:
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"
        ordering = ['-created_at']


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist', verbose_name="کاربر")
    products = models.ManyToManyField(Product, related_name='wishlists', verbose_name="محصولات مورد علاقه")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"لیست علاقه‌مندی {self.user.username}"
    


