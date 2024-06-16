from django import forms 
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product
from .models import CartItem

class SignupForm(UserCreationForm):
    username = forms.CharField(label='Phone Number', widget=forms.TextInput(attrs={'placeholder': 'Phone Number'}))
    email = forms.CharField(label='email', widget=forms.TextInput(attrs={'placeholder': 'email...'}))
    password1 = forms.CharField(label='password1', widget=forms.TextInput(attrs={'placeholder': 'Password...'}))
    password2 = forms.CharField(label='password2', widget=forms.TextInput(attrs={'placeholder': 'confirm password...'}))
    
    class Meta:
        model = User 
        fields = ['username', 'email', 'password1', 'password2']

class LoginForm(forms.Form):
     username = forms.CharField(label='Phone Number', widget=forms.TextInput(attrs={'placeholder': 'Phone Number...'}))
     password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter Password...'}))

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image', 'category']
        
class AddToCartForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']    

class AddStaffForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']

    def save(self, commit=True):
        user = super(AddStaffForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_staff = True
        if commit:
            user.save()
        return user          