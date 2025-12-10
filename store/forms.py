# در فایل store/forms.py

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import ShippingAddress
from .models import ShippingAddress, Customer

class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(
        label="شماره موبایل",
        max_length=11,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '0912xxxxxxx',
            'style': 'direction: ltr; text-align: left;' # شماره موبایل چپ‌چین باشد بهتر است
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'phone_number')
        help_texts = {
            'username': 'نام کاربری می‌تواند شامل حروف و اعداد باشد.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # فارسی سازی لیبل‌ها و متون راهنما
        self.fields['username'].label = "نام کاربری"
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'نام کاربری خود را وارد کنید'
        })

        # حذف متن‌های راهنمای طولانی پسورد که ظاهر را خراب می‌کنند (اختیاری)
        # یا می‌توانید آن‌ها را ترجمه کنید. اینجا برای زیبایی متن کوتاه گذاشتیم:
        self.fields['password1'].label = "رمز عبور"
        self.fields['password1'].help_text = "رمز عبور باید حداقل ۸ کاراکتر باشد و خیلی ساده نباشد."
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': '********'
        })

        self.fields['password2'].label = "تکرار رمز عبور"
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': '********'
        })

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if Customer.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("این شماره موبایل قبلاً ثبت شده است.")
        if not (len(phone) == 11 and phone.startswith('09')):
            raise forms.ValidationError("فرمت شماره موبایل صحیح نیست.")
        return phone

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