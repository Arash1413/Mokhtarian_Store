# در فایل store/forms.py

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import ShippingAddress

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',) # می‌توانید فیلدهای دیگری مثل first_name, last_name را هم اضافه کنید


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "نام کاربری"
        self.fields['password2'].label = "تکرار رمز عبور"

class ShippingForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        # فیلدهای جدید را به لیست اضافه کنید
        fields = ['full_name', 'phone_number', 'address', 'city', 'state', 'zipcode']
        widgets = {
            # ویجت‌های جدید را اضافه کنید
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام و نام خانوادگی'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره تماس'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'آدرس کامل'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شهر'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'استان'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد پستی'}),
        }