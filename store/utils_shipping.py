# store/utils_shipping.py

def calculate_shipping_cost(total_weight_grams):
    """
    محاسبه هزینه پست بر اساس وزن به گرم
    """
    if total_weight_grams == 0:
        return 0
    
    # تبدیل به تومان طبق سناریوی شما
    if total_weight_grams < 500:
        return 70000
    elif total_weight_grams < 1000: # زیر 1 کیلو
        return 100000
    elif total_weight_grams < 2000: # زیر 2 کیلو
        return 150000
    elif total_weight_grams < 3000: # زیر 3 کیلو
        return 200000
    elif total_weight_grams < 4000: # زیر 4 کیلو
        return 250000
    else:
        # برای وزن‌های بالاتر از 4 کیلو، مثلا هر کیلو 30 تومن اضافه شود (اختیاری)
        # فعلا روی همان 250 قفل می‌کنیم یا طبق سیاست شما تغییر دهید
        return 300000