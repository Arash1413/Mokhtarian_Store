from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from simple_history.models import HistoricalRecords



# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True)

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
    

# class Customer(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     name = models.CharField(max_length=200, null=True)
#     email = models.CharField(max_length=200, null=True)
#     phone_number = models.CharField(max_length=15, blank=True, null=True)

#     def __str__(self):
#         return self.user.get_full_name() or self.user.username

class Customer(models.Model):
    # --- تغییرات کلیدی ---
    # 1. OneToOneField را به ForeignKey تغییر دهید.
    # 2. null=True و blank=True را اضافه کنید.
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # --- پایان تغییرات ---

    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True) # اضافه کردن unique=True

    def __str__(self):
        # اصلاح تابع __str__ برای مدیریت کاربرانی که user ندارند
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.phone_number or f"Customer {self.id}"
    

class Order(models.Model):
    SHIPPING_CHOICES = [
        ('mahex', 'ماهکس (پس‌کرایه)'),
        ('post', 'پست پیشتاز'),
    ]
    # ... فیلدهای قبلی ...
    shipping_method = models.CharField(max_length=20, choices=SHIPPING_CHOICES, default='mahex')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=200, null=True)
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
    # on_delete به PROTECT تغییر کرد تا از حذف محصول و ایجاد خطا جلوگیری شود
    product = models.ForeignKey(Product, on_delete=models.PROTECT) 
    # on_delete به CASCADE تغییر کرد که منطقی‌تر است
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    # نوع فیلد و مقدار پیش‌فرض آن بهبود یافت
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
    full_name = models.CharField(max_length=200, null=True)  # <-- فیلد جدید
    phone_number = models.CharField(max_length=20, null=True) # <-- فیلد جدید
    address = models.CharField(max_length=200, null=False)
    city = models.CharField(max_length=200, null=False)
    state = models.CharField(max_length=200, null=False) # استان
    zipcode = models.CharField(max_length=200, null=False) # کد پستی
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
    



    


