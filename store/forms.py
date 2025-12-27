# در فایل store/forms.py

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import ShippingAddress
from .models import ShippingAddress, Customer, Brand
from .models import Review



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
    security_question = forms.CharField(
        label="سوال امنیتی (خودتان طرح کنید)",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'مثلاً: نام اولین مدرسه من؟ یا رنگ مورد علاقه؟'
        })
    )
    
    security_answer = forms.CharField(
        label="پاسخ سوال امنیتی",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'پاسخ را وارد کنید (این پاسخ محرمانه می‌ماند)'
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
    SHIPPING_CHOICES = [
        ('mahex', 'ماهکس (پس‌کرایه - هزینه درب منزل)'),
        ('post', 'پست پیشتاز (پیش پرداخت)'),
    ]
    shipping_method = forms.ChoiceField(
        choices=SHIPPING_CHOICES, 
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="شیوه ارسال"
    )
    class Meta:
        model = ShippingAddress
        # فیلدهای جدید را به لیست اضافه کنید
        fields = ['full_name', 'phone_number', 'address', 'city', 'state', 'zipcode']
        widgets = {
            # ویجت‌های جدید را اضافه کنید
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام و نام خانوادگی'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره تماس'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'آدرس کامل'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'id': 'state_input'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'id': 'city_input'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد پستی'}),
        }


class UsernameRecoveryForm(forms.Form):
    identifier = forms.CharField(
        label="نام کاربری یا شماره موبایل",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام کاربری یا 0912...'})
    )

class SecurityAnswerForm(forms.Form):
    answer = forms.CharField(
        label="پاسخ شما",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'پاسخ سوال امنیتی خود را بنویسید'})
    )

class PasswordResetForm(forms.Form):
    new_password = forms.CharField(
        label="رمز عبور جدید",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    confirm_password = forms.CharField(
        label="تکرار رمز عبور جدید",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("رمز عبور و تکرار آن مطابقت ندارند.")
        
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['subject', 'comment', 'rating']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان نظر'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'متن نظر خود را بنویسید...'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }


class ProductFilterForm(forms.Form):
    # فیلتر قیمت
    min_price = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'از تومان'}))
    max_price = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'تا تومان'}))
    
    # فیلتر موجودی (چک‌باکس)
    in_stock = forms.BooleanField(required=False, label="فقط کالاهای موجود", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    # فیلتر برند (چک‌باکس چند انتخابی)
    brands = forms.ModelMultipleChoiceField(
        queryset=Brand.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="برندها"
    )