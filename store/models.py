from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


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
        
class Product(models.Model):
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
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

    class Meta:
        ordering = ('-created',)
        indexes = [
            models.Index(fields=['id', 'slug']),
        ]

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])

    def __str__(self):
        return self.name
    

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=200, null=True)

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
    


