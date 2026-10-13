from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import LoginForm, InviteUserForm

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def invite_user(request):
    form = InviteUserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        email = form.cleaned_data['email']
        temp_password = User.objects.make_random_password(length=10)
        user = User.objects.create_user(username=username, email=email, password=temp_password)
        messages.success(request, f'User {username} created! Temp password: {temp_password}')
        return redirect('invite_user')
    return render(request, 'accounts/invite_user.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return redirect('login')
