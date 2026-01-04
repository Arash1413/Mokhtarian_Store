from decimal import Decimal
from django.conf import settings
from store.models import Product, Coupon

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.coupon_id = self.session.get('coupon_id')

    def add(self, product, quantity=1, override_quantity=False):
        
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            quantity = 1

        
        if quantity < 1:
            return 
        

        product_id = str(product.id)
        if product_id not in self.cart:
           
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
        cart = {k: v.copy() for k, v in self.cart.items()}

        for product in products:
            item = cart[str(product.id)]
            item['product'] = product
            
            qty = int(item['quantity'])
            
            current_price = product.get_current_price(qty)
            
            item['price'] = Decimal(current_price)
            item['total_price'] = item['price'] * qty
            
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
            price = product.get_current_price(qty)
            total += price * qty
            
        return total

    def get_total_weight(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        total_weight = 0
        for product in products:
            cart_item = self.cart[str(product.id)]
            qty = cart_item['quantity']
            total_weight += (product.weight * qty)
        return total_weight
    
    @property
    def coupon(self):
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
                pass
        return None

    def get_discount(self):
        if self.coupon:
            valid_products = self.coupon.products.all()
            valid_product_ids = set(valid_products.values_list('id', flat=True))
            
            discountable_amount = 0
            
            product_ids = self.cart.keys()
            products_in_cart = Product.objects.filter(id__in=product_ids)

            for product in products_in_cart:
                if not valid_product_ids or product.id in valid_product_ids:
                    
                    item = self.cart[str(product.id)]
                    qty = int(item['quantity'])
                    
                    price = product.get_current_price(qty)
                    
                    discountable_amount += price * qty

            return (self.coupon.discount / Decimal(100)) * discountable_amount
            
        return Decimal(0)

    def get_total_price_before_discount(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        total = 0
        for product in products:
            item = self.cart[str(product.id)]
            qty = int(item['quantity'])
            price = product.get_current_price(qty)
            total += price * qty
        return total

    def get_total_price(self):
        return self.get_total_price_before_discount() - self.get_discount()

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()