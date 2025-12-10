from django.contrib import admin
from .models import Category, Product, Customer, Order, OrderItem, Attribute, ProductAttribute, ShippingAddress, Brand

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1 # ب

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'wholesale_price', 'wholesale_min_qty', 'stock', 'available']
    list_filter = ['available', 'created', 'updated', 'is_bestseller', 'brand']
    list_editable = ['price', 'wholesale_price', 'wholesale_min_qty', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductAttributeInline]
    search_fields = ['name', 'description']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'email', 'phone_number']
    search_fields = ['user__username', 'name', 'phone_number']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

class ShippingAddressInline(admin.StackedInline): # از StackedInline برای نمایش بهتر استفاده می‌کنیم
    model = ShippingAddress
    can_delete = False # معمولا نمی‌خواهیم آدرس را از اینجا حذف کنیم
    verbose_name_plural = 'آدرس ارسال'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'tracking_code', 'date_ordered', 'complete', 'get_cart_total']
    list_filter = ['status', 'complete', 'date_ordered'] # فیلتر بر اساس وضعیت اضافه شد
    search_fields = ['id', 'customer__name', 'tracking_code']
    list_editable = ['status', 'tracking_code'] # این خط اجازه ویرایش سریع را می‌دهد
    inlines = [ShippingAddressInline, OrderItemInline]

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

