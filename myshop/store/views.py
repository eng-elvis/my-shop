# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .forms import SignupForm, LoginForm, ProductForm, AddToCartForm, AddStaffForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Cart, CartItem, Category
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import views as auth_views
from django.db.models import Q


@login_required(login_url='login')
@staff_member_required
def user_list(request):
    users = User.objects.all()
    return render(request, 'user_list.html', {'users': users})

@login_required(login_url='login')
@staff_member_required
def add_staff_member(request):
    if request.method == 'POST':
        form = AddStaffForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member created successfully')
            return redirect('user_list')
    else:
        form = AddStaffForm()
    return render(request, 'add_staff.html', {'form': form})

def user_register(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('username')
            messages.success(request, 'Account was created for ' + user)
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.info(request, 'Username or password is incorrect')
                context = {'form': form}
                return render(request, 'login.html', context)
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

# views.py
@login_required(login_url='login')
def home(request):
    query = request.GET.get('q')
    products_by_category = {}
    categories = Category.objects.all()

    if query:
        search_results = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
        products_by_category['Search'] = search_results

    for category in categories:
        products = Product.objects.filter(category=category)
        products_by_category[category.name] = products

    return render(request, 'home.html', {'products_by_category': products_by_category, 'query': query})


@login_required(login_url='login')
def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def add_product_view(request):
    if not request.user.is_staff:
        return redirect('home')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ProductForm()
    
    return render(request, 'add_product.html', {'form': form})

@login_required
def delete_product_view(request, product_id):
    if not request.user.is_staff:
        return redirect('home')

    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.delete()
        return redirect('home')
    
    return render(request, 'delete_product.html', {'product': product})

@login_required(login_url='login')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
            if not created:
                cart_item.quantity += quantity
            else:
                cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, f'Added {quantity} of {product.name} to your cart')
            return redirect('view_cart')
    else:
        form = AddToCartForm()

    return render(request, 'add_to_cart.html', {'form': form, 'product': product})

@login_required
def view_cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        total_price = sum(item.total_price for item in cart_items)
    except Cart.DoesNotExist:
        cart_items = []
        total_price = 0

    print(f"Cart items: {cart_items}")
    print(f"Total price: {total_price}")

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }

    return render(request, 'view_cart.html', context)

@login_required(login_url='login')
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    if request.method == 'POST':
        # Handle payment processing here
        cart_items.delete()  # Clear the cart after payment
        messages.success(request, 'Thank you for your purchase!')
        return redirect('home')
    total_price = sum([item.total_price for item in cart_items])
    return render(request, 'checkout.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required(login_url='login')
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, f'Removed {cart_item.product.name} from your cart')
    return redirect('view_cart')

def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(request=request)
            return render(request, 'password_reset_done.html')
    else:
        form = PasswordResetForm()
    return render(request, 'password_reset_form.html', {'form': form})

User = get_user_model()

def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                return redirect('password_reset_complete')
        else:
            form = SetPasswordForm(user)
        return render(request, 'password_reset_confirm.html', {'form': form})
    else:
        raise Http404("Invalid password reset link")
            
