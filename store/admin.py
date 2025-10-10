from django.contrib import admin
from .models import Category, Product, Customer, Order, OrderItem, Attribute, ProductAttribute, ShippingAddress

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1 # ب

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price', 'old_price', 'is_bestseller', 'stock', 'available']
    list_filter = ['available', 'created', 'updated', 'is_bestseller']
    list_editable = ['price', 'old_price', 'stock', 'available', 'is_bestseller']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductAttributeInline]

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
    list_display = ['id', 'customer', 'date_ordered', 'complete', 'get_cart_total', 'get_cart_items']
    list_filter = ['complete', 'date_ordered']
    search_fields = ['id', 'customer__name']
    inlines = [ShippingAddressInline, OrderItemInline]

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

