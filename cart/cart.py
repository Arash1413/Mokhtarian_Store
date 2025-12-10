from decimal import Decimal
from django.conf import settings
from store.models import Product

class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def get_total_weight(self):
        """
        محاسبه وزن کل محصولات درون سبد خرید
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        total_weight = 0
        
        for product in products:
            cart_item = self.cart[str(product.id)]
            qty = cart_item['quantity']
            total_weight += (product.weight * qty)
            
        return total_weight

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            # تغییر کلیدی: قیمت را به رشته تبدیل می‌کنیم
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        # mark the session as "modified" to make sure it gets saved
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    # def __iter__(self):
    #     """
    #     Iterate over the items in the cart and get the products
    #     from the database.
    #     This method prepares items for display, without modifying the session cart.
    #     """
    #     product_ids = self.cart.keys()
    #     products = Product.objects.filter(id__in=product_ids)

    #     # یک دیکشنری برای دسترسی سریع به محصولات بر اساس ID
    #     products_map = {str(p.id): p for p in products}

    #     # روی یک کپی از سبد خرید حلقه بزنید
    #     for product_id, item_data in self.cart.items():
    #         product = products_map.get(product_id)
    #         if product:
    #             # یک دیکشنری جدید برای هر آیتم بسازید تا session اصلی تغییر نکند
    #             item = item_data.copy()
    #             item['product'] = product
    #             price = Decimal(item['price'])
    #             item['total_price'] = price * item['quantity']
                
    #             # این yield دیکشنری جدید و تمیز را برمی‌گرداند
    #             yield item
    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        products_map = {str(p.id): p for p in products}

        for product_id, item_data in self.cart.items():
            product = products_map.get(product_id)
            if product:
                item = item_data.copy()
                item['product'] = product
                price = Decimal(item['price'])
                item['total_price'] = price * item['quantity']
                
                # ========== خط تشخیصی ==========
                # print(f"DEBUG: Yielding item for product: {product.name}")
                # ===============================

                yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        # remove cart from session
        del self.session[settings.CART_SESSION_ID]
        self.save()