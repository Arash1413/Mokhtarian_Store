# store/utils_shipping.py

def calculate_shipping_cost(total_weight_grams):
    """
    محاسبه هزینه پست بر اساس وزن به گرم
    """
    if total_weight_grams == 0:
        return 0
    
    # تبدیل به تومان طبق سناریوی شما
    if total_weight_grams < 500:
        return 85000
    elif total_weight_grams < 1000: # زیر 1 کیلو
        return 115000
    elif total_weight_grams < 2000: # زیر 2 کیلو
        return 165000
    elif total_weight_grams < 3000: # زیر 3 کیلو
        return 250000
    elif total_weight_grams < 4000: # زیر 4 کیلو
        return 265000
    elif total_weight_grams < 5000: # زیر 4 کیلو
        return 315000
    elif total_weight_grams < 6000: # زیر 4 کیلو
        return 365000
    elif total_weight_grams < 7000: # زیر 4 کیلو
        return 415000
    elif total_weight_grams < 8000: # زیر 4 کیلو
        return 465000
    elif total_weight_grams < 9000: # زیر 4 کیلو
        return 515000
    elif total_weight_grams < 10000: # زیر 4 کیلو
        return 565000
    elif total_weight_grams < 11000: # زیر 4 کیلو
        return 615000
    elif total_weight_grams < 12000: # زیر 4 کیلو
        return 665000
    elif total_weight_grams < 13000: # زیر 4 کیلو
        return 715000
    elif total_weight_grams < 4000: # زیر 4 کیلو
        return 765000
    elif total_weight_grams < 15000: # زیر 4 کیلو
        return 815000
    elif total_weight_grams < 16000: # زیر 4 کیلو
        return 865000
    elif total_weight_grams < 17000: # زیر 4 کیلو
        return 915000
    elif total_weight_grams < 18000: # زیر 4 کیلو
        return 965000
    else:
        # برای وزن‌های بالاتر از 4 کیلو، مثلا هر کیلو 30 تومن اضافه شود (اختیاری)
        # فعلا روی همان 250 قفل می‌کنیم یا طبق سیاست شما تغییر دهید
        return 1000000