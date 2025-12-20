# from django.contrib import admin
# from .models import Category, Product, Customer, Order, OrderItem, Attribute, ProductAttribute, ShippingAddress, Brand

# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ['name', 'slug']
#     prepopulated_fields = {'slug': ('name',)}

# class ProductAttributeInline(admin.TabularInline):
#     model = ProductAttribute
#     extra = 1 # ب

# @admin.register(Brand)
# class BrandAdmin(admin.ModelAdmin):
#     list_display = ('name',)
#     search_fields = ('name',)

# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ['name', 'price', 'wholesale_price', 'wholesale_min_qty', 'stock', 'available']
#     list_filter = ['available', 'created', 'updated', 'is_bestseller', 'brand']
#     list_editable = ['price', 'wholesale_price', 'wholesale_min_qty', 'stock', 'available']
#     prepopulated_fields = {'slug': ('name',)}
#     inlines = [ProductAttributeInline]
#     search_fields = ['name', 'description']

# @admin.register(Customer)
# class CustomerAdmin(admin.ModelAdmin):
#     list_display = ['user', 'name', 'email', 'phone_number']
#     search_fields = ['user__username', 'name', 'phone_number']

# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     raw_id_fields = ['product']

# class ShippingAddressInline(admin.StackedInline): # از StackedInline برای نمایش بهتر استفاده می‌کنیم
#     model = ShippingAddress
#     can_delete = False # معمولا نمی‌خواهیم آدرس را از اینجا حذف کنیم
#     verbose_name_plural = 'آدرس ارسال'

# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['id', 'customer', 'status', 'tracking_code', 'date_ordered', 'complete', 'get_cart_total']
#     list_filter = ['status', 'complete', 'date_ordered'] # فیلتر بر اساس وضعیت اضافه شد
#     search_fields = ['id', 'customer__name', 'tracking_code']
#     list_editable = ['status', 'tracking_code'] # این خط اجازه ویرایش سریع را می‌دهد
#     inlines = [ShippingAddressInline, OrderItemInline]

# @admin.register(Attribute)
# class AttributeAdmin(admin.ModelAdmin):
#     list_display = ['name']
#     search_fields = ['name']


from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Category, Product, Customer, Order, OrderItem, Attribute, ProductAttribute, ShippingAddress, Brand, Coupon, Review
from .models import FAQ

# تنظیمات هدر پنل ادمین
admin.site.site_header = "مدیریت فروشگاه مختاریان"
admin.site.site_title = "پنل مدیریت"
admin.site.index_title = "به پنل مدیریت خوش آمدید"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'تعداد محصولات'

class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1
    # classes = ['collapse'] # قابلیت جمع شدن برای شلوغ نشدن صفحه

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count')
    search_fields = ('name',)

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'تعداد محصولات'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['show_image', 'name', 'category', 'price', 'stock', 'available', 'is_bestseller', 'updated']
    list_filter = ['available', 'is_bestseller', 'category', 'brand', 'created']
    list_editable = ['price', 'stock', 'available', 'is_bestseller']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductAttributeInline]
    search_fields = ['name', 'description']
    list_per_page = 20
    
    # گروه‌بندی فیلدها در صفحه ویرایش
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('category', 'brand', 'name', 'slug', 'image', 'description')
        }),
        ('قیمت‌گذاری و موجودی', {
           'fields': ('price', 'old_price', 'wholesale_price', 'wholesale_min_qty', 'stock', 'weight', 'available')
        }),
        ('محدودیت‌های سفارش', {
            'fields': ('min_order_quantity', 'max_order_quantity'),
            'classes': ('collapse',)
        }),
        ('تنظیمات فروش', {
            'fields': ('is_bestseller',),
            'classes': ('collapse',)
        }),
    )

    def show_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "بدون تصویر"
    show_image.short_description = "تصویر"

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'order_count']
    search_fields = ['name', 'phone_number', 'user__username']

    def order_count(self, obj):
        return obj.order_set.count()
    order_count.short_description = "تعداد سفارشات"

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['get_total'] # نمایش قیمت کل هر ردیف به صورت فقط خواندنی

class ShippingAddressInline(admin.StackedInline):
    model = ShippingAddress
    can_delete = False
    verbose_name_plural = 'آدرس ارسال'
    classes = ['collapse']

# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['id', 'customer_link', 'status_colored', 'total_price_display', 'date_ordered_jalali', 'tracking_code']
#     list_filter = ['status', 'date_ordered', 'complete']
#     search_fields = ['id', 'customer__name', 'tracking_code', 'customer__phone_number']
#     list_editable = ['status', 'tracking_code']
#     inlines = [ShippingAddressInline, OrderItemInline]
#     readonly_fields = ['date_ordered', 'transaction_id']
#     list_per_page = 15

#     # گروه‌بندی فیلدها
#     fieldsets = (
#         ('اطلاعات مشتری و وضعیت', {
#             'fields': ('customer', 'status', 'tracking_code', 'complete', 'transaction_id')
#         }),
#         ('اطلاعات مالی', {
#             'fields': ('total_price', 'shipping_method', 'shipping_cost')
#         }),
#         ('تاریخچه', {
#             'fields': ('date_ordered',),
#         }),
#     )

#     # نمایش وضعیت با رنگ‌بندی
#     def status_colored(self, obj):
#         colors = {
#             'pending': 'orange',
#             'paid': 'blue',
#             'processing': 'purple',
#             'shipped': 'teal',
#             'delivered': 'green',
#             'cancelled': 'red',
#         }
#         color = colors.get(obj.status, 'black')
#         return format_html(
#             '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 10px; font-weight: bold;">{}</span>',
#             color,
#             obj.get_status_display()
#         )
#     status_colored.short_description = 'وضعیت'

#     # لینک به صفحه مشتری
#     def customer_link(self, obj):
#         if obj.customer:
#             return obj.customer.name or obj.customer.phone_number
#         return "-"
#     customer_link.short_description = "مشتری"

#     def total_price_display(self, obj):
#         return f"{int(obj.total_price or 0):,} تومان"
#     total_price_display.short_description = "مبلغ کل"

#     def date_ordered_jalali(self, obj):
#         return obj.date_ordered.strftime("%Y/%m/%d %H:%M")
#     date_ordered_jalali.short_description = "تاریخ سفارش"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # تغییر: 'status_colored' را حذف و 'status' را اضافه کردیم
    # چون فیلد status در list_editable است، باید حتما اینجا هم باشد
    list_display = ['id', 'customer_link', 'status', 'total_price_display', 'date_ordered_jalali', 'tracking_code']
    
    list_filter = ['status', 'date_ordered', 'complete']
    search_fields = ['id', 'customer__name', 'tracking_code', 'customer__phone_number']
    
    # این خط باعث می‌شود در همان صفحه لیست، وضعیت و کد رهگیری قابل تغییر باشند
    list_editable = ['status', 'tracking_code']
    
    inlines = [ShippingAddressInline, OrderItemInline]
    readonly_fields = ['date_ordered', 'transaction_id']
    list_per_page = 15

    # گروه‌بندی فیلدها برای صفحه جزئیات
    fieldsets = (
        ('اطلاعات مشتری و وضعیت', {
            'fields': ('customer', 'status', 'status_colored', 'tracking_code', 'complete', 'transaction_id')
        }),
        ('اطلاعات مالی', {
            'fields': ('total_price', 'shipping_method', 'shipping_cost')
        }),
        ('تاریخچه', {
            'fields': ('date_ordered',),
        }),
    )
    
    # برای اینکه وضعیت رنگی را در صفحه جزئیات (داخل سفارش) ببینیم، آن را فقط خواندنی می‌کنیم
    readonly_fields = ['date_ordered', 'transaction_id', 'status_colored']

    # نمایش وضعیت با رنگ‌بندی (برای استفاده در صفحه جزئیات)
    def status_colored(self, obj):
        colors = {
            'pending': 'orange',
            'paid': 'blue',
            'processing': 'purple',
            'shipped': 'teal',
            'delivered': 'green',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 10px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'وضعیت فعلی (رنگی)'

    # لینک به صفحه مشتری
    def customer_link(self, obj):
        if obj.customer:
            return obj.customer.name or obj.customer.phone_number
        return "-"
    customer_link.short_description = "مشتری"

    def total_price_display(self, obj):
        return f"{int(obj.total_price or 0):,} تومان"
    total_price_display.short_description = "مبلغ کل"

    def date_ordered_jalali(self, obj):
        return obj.date_ordered.strftime("%Y/%m/%d %H:%M")
    date_ordered_jalali.short_description = "تاریخ سفارش"

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']



@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'sort_order', 'is_active']
    list_editable = ['sort_order', 'is_active']
    search_fields = ['question', 'answer']

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'valid_from', 'valid_to', 'discount', 'active']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']
    
    # 👇 این خط را اضافه کنید تا انتخاب محصولات راحت شود 👇
    filter_horizontal = ['products'] 
    
    fieldsets = (
        (None, {
            'fields': ('code', 'discount', 'active')
        }),
        ('محدودیت‌ها', {
            'fields': ('products',),
            'description': 'اگر محصولی انتخاب نکنید، کد تخفیف روی تمام محصولات اعمال می‌شود.'
        }),
        ('زمان اعتبار', {
            'fields': ('valid_from', 'valid_to'),
        }),
    )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['subject', 'rating', 'user', 'product', 'status']
    list_editable = ['status'] # برای تایید سریع در لیست
    list_filter = ['status', 'created_at']
    readonly_fields = ['user', 'product', 'rating', 'subject', 'comment'] # تا ادمین نتواند نظر کاربر را تغییر دهد (اختیاری)