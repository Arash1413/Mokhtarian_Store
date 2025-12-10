from decimal import Decimal
from django.conf import settings
from store.models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        # --- اصلاح امنیتی شروع ---
        # اطمینان از اینکه تعداد حتما یک عدد صحیح است
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            quantity = 1

        # اگر تعداد کمتر از 1 بود، یا آن را نادیده بگیر یا به 1 تغییر بده
        # در اینجا اگر کاربر عدد منفی فرستاد، ما هیچ کاری نمی‌کنیم (return) تا امنیت حفظ شود
        if quantity < 1:
            return 
        # --- اصلاح امنیتی پایان ---

        product_id = str(product.id)
        if product_id not in self.cart:
            # قیمت اولیه را ذخیره می‌کنیم، اما محاسبات اصلی داینامیک انجام می‌شود
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
            
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        اینجا تصمیم می‌گیریم چه قیمتی (عادی یا عمده) به کاربر نمایش داده شود
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            item = cart[str(product.id)]
            item['product'] = product
            
            # --- منطق قیمت عمده ---
            qty = int(item['quantity'])
            
            # استفاده از متدی که در مدل نوشتیم
            current_price = product.get_current_price(qty)
            
            # تبدیل به Decimal برای محاسبات
            item['price'] = Decimal(current_price)
            item['total_price'] = item['price'] * qty
            
            # یک پرچم برای نمایش در قالب HTML که آیا قیمت عمده اعمال شده یا نه
            item['is_wholesale_applied'] = (current_price == product.wholesale_price)
            
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        محاسبه قیمت کل با در نظر گرفتن تخفیف‌های عمده
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        total = 0
        
        for product in products:
            item = self.cart[str(product.id)]
            qty = int(item['quantity'])
            # دریافت قیمت هوشمند بر اساس تعداد
            price = product.get_current_price(qty)
            total += price * qty
            
        return total

    def get_total_weight(self):
        # ... کد قبلی وزن ...
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        total_weight = 0
        for product in products:
            cart_item = self.cart[str(product.id)]
            qty = cart_item['quantity']
            total_weight += (product.weight * qty)
        return total_weight

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()