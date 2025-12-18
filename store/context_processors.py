# store/context_processors.py
from .models import Category
from .models import FAQ

def categories(request):
    return {
        'categories': Category.objects.all()
    }


def faq_list(request):
    return {
        'faqs': FAQ.objects.filter(is_active=True)
    }