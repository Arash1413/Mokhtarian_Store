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
    elif total_weight_grams < 5000: # زیر 4 کیلو
        return 300000
    elif total_weight_grams < 6000: # زیر 4 کیلو
        return 350000
    elif total_weight_grams < 7000: # زیر 4 کیلو
        return 400000
    elif total_weight_grams < 8000: # زیر 4 کیلو
        return 450000
    elif total_weight_grams < 9000: # زیر 4 کیلو
        return 500000
    elif total_weight_grams < 10000: # زیر 4 کیلو
        return 550000
    elif total_weight_grams < 11000: # زیر 4 کیلو
        return 600000
    elif total_weight_grams < 12000: # زیر 4 کیلو
        return 650000
    elif total_weight_grams < 13000: # زیر 4 کیلو
        return 700000
    elif total_weight_grams < 4000: # زیر 4 کیلو
        return 750000
    elif total_weight_grams < 15000: # زیر 4 کیلو
        return 800000
    elif total_weight_grams < 16000: # زیر 4 کیلو
        return 850000
    elif total_weight_grams < 17000: # زیر 4 کیلو
        return 900000
    elif total_weight_grams < 18000: # زیر 4 کیلو
        return 950000
    else:
        # برای وزن‌های بالاتر از 4 کیلو، مثلا هر کیلو 30 تومن اضافه شود (اختیاری)
        # فعلا روی همان 250 قفل می‌کنیم یا طبق سیاست شما تغییر دهید
        return 1000000