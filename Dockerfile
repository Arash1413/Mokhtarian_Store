# استفاده از پایتون نسخه سبک
FROM python:3.10-slim

# تنظیم متغیرهای محیطی برای جلوگیری از ساخت فایل‌های pyc و بافرینگ
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# تنظیم دایرکتوری کاری داخل کانتینر
WORKDIR /app

# نصب وابستگی‌های سیستم عامل (برای برخی پکیج‌های پایتون و Postgres اگر بعدا بخواهید)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# کپی کردن فایل نیازمندی‌ها و نصب آن‌ها
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# کپی کردن کل پروژه به داخل کانتینر
COPY . /app/

# پورت که کانتینر روی آن گوش می‌دهد (فقط جهت اطلاع)
EXPOSE 8000

# دستور اجرای پیش‌فرض (توسط docker-compose بازنویسی می‌شود اما بودنش خوب است)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]