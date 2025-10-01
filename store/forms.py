# در فایل store/forms.py

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import ShippingAddress

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email') # می‌توانید فیلدهای دیگری مثل first_name, last_name را هم اضافه کنید



class ShippingForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['address', 'city', 'state', 'zipcode']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'آدرس کامل'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شهر'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'استان'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد پستی'}),
        }