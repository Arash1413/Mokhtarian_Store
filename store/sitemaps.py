# store/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category

class ProductSitemap(Sitemap):
    changefreq = 'daily'  # هر چند وقت یکبار تغییر می‌کند
    priority = 0.9        # اولویت (از 0 تا 1)

    def items(self):
        return Product.objects.filter(available=True)

    def lastmod(self, obj):
        return obj.updated

class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Category.objects.all()

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return ['store:product_list', 'store:about_page'] # نام ویوهای استاتیک

    def location(self, item):
        return reverse(item)