#!/bin/bash
# Builds ALL files for Warranty RMA Tracker v2
set -e
cd ~/Warranty_RMA_Tracker
rm -rf apps core manage.py .env requirements.txt
mkdir -p core apps/accounts apps/home apps/rma apps/templates/{layouts,includes,accounts,home,rma} apps/static

# --- requirements.txt ---
cat > requirements.txt << 'EOF'
Django==3.2.6
gunicorn==20.1.0
python-decouple==3.5
whitenoise==5.3.0
EOF

# --- .env ---
cat > .env << 'EOF'
SECRET_KEY=django-insecure-rma-tracker-v2-2024-change-me
DEBUG=True
EOF

# --- Core files ---
cat > core/__init__.py << 'EOF'
EOF

cat > core/wsgi.py << 'EOF'
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
application = get_wsgi_application()
EOF

cat > core/settings.py << 'EOF'
import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config('SECRET_KEY', default='change-me')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'apps.accounts','apps.home','apps.rma',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'apps' / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]
WSGI_APPLICATION = 'core.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}}]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Chicago'
USE_I18N = True; USE_L10N = True; USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'apps' / 'static']
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EOF

cat > core/urls.py << 'EOF'
from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('rma/', include('apps.rma.urls')),
    path('', include('apps.home.urls')),
]
EOF

# --- Init files ---
for d in apps apps/accounts apps/home apps/rma; do touch $d/__init__.py; done

# --- Accounts app ---
cat > apps/accounts/views.py << 'EOF'
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
EOF

cat > apps/accounts/forms.py << 'EOF'
from django import forms
class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
class InviteUserForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
EOF

cat > apps/accounts/urls.py << 'EOF'
from django.urls import path
from . import views
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('invite/', views.invite_user, name='invite_user'),
]
EOF

# --- Home app (Warranty Claims) ---
cat > apps/home/models.py << 'EOF'
from django.db import models
from django.contrib.auth.models import User

STATUS_CHOICES = [('NEW','New'),('FILED','Filed'),('PAID','Paid')]

class WarrantyClaim(models.Model):
    job_number = models.CharField(max_length=50, blank=True, null=True)
    tech_name = models.CharField(max_length=100, blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    claim_date = models.DateField(blank=True, null=True)
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='NEW')
    vendor = models.CharField(max_length=100, blank=True, null=True)
    vendor_submission_method = models.CharField(max_length=100, blank=True, null=True)
    vendor_confirmation_number = models.CharField(max_length=100, blank=True, null=True)
    vendor_submitted_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claims')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"Claim #{self.id} - {self.customer_name or 'N/A'} ({self.get_status_display()})"
EOF

cat > apps/home/forms.py << 'EOF'
from django import forms
from .models import WarrantyClaim

class WarrantyClaimForm(forms.ModelForm):
    class Meta:
        model = WarrantyClaim
        fields = ['job_number','tech_name','customer_name','claim_date','claim_amount','status','vendor','vendor_submission_method','vendor_confirmation_number','vendor_submitted_date','notes']
        widgets = {
            'job_number': forms.TextInput(attrs={'class':'form-control'}),
            'tech_name': forms.TextInput(attrs={'class':'form-control'}),
            'customer_name': forms.TextInput(attrs={'class':'form-control'}),
            'claim_date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'claim_amount': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'status': forms.Select(attrs={'class':'form-control'}),
            'vendor': forms.TextInput(attrs={'class':'form-control'}),
            'vendor_submission_method': forms.TextInput(attrs={'class':'form-control'}),
            'vendor_confirmation_number': forms.TextInput(attrs={'class':'form-control'}),
            'vendor_submitted_date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'notes': forms.Textarea(attrs={'class':'form-control','rows':3}),
        }
EOF

cat > apps/home/views.py << 'EOF'
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Sum
from .models import WarrantyClaim
from .forms import WarrantyClaimForm

@login_required
def index(request):
    claims = WarrantyClaim.objects.all() if request.user.is_superuser else WarrantyClaim.objects.filter(user=request.user)
    ctx = {
        'total_claims': claims.count(),
        'new_count': claims.filter(status='NEW').count(),
        'filed_count': claims.filter(status='FILED').count(),
        'paid_count': claims.filter(status='PAID').count(),
        'total_amount': claims.aggregate(Sum('claim_amount'))['claim_amount__sum'] or 0,
    }
    return render(request, 'home/index.html', ctx)

@login_required
def claim_list(request):
    claims = WarrantyClaim.objects.all() if request.user.is_superuser else WarrantyClaim.objects.filter(user=request.user)
    return render(request, 'home/claim_list.html', {'claims': claims})

@login_required
def claim_add(request):
    form = WarrantyClaimForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        claim = form.save(commit=False)
        claim.user = request.user
        claim.save()
        messages.success(request, 'Claim added successfully!')
        return redirect('claim_list')
    return render(request, 'home/claim_form.html', {'form': form, 'title': 'Add Warranty Claim'})

@login_required
def claim_edit(request, pk):
    claim = get_object_or_404(WarrantyClaim, pk=pk) if request.user.is_superuser else get_object_or_404(WarrantyClaim, pk=pk, user=request.user)
    form = WarrantyClaimForm(request.POST or None, instance=claim)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Claim updated successfully!')
        return redirect('claim_list')
    return render(request, 'home/claim_form.html', {'form': form, 'title': 'Edit Warranty Claim'})

@login_required
def claim_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete claims.')
        return redirect('claim_list')
    claim = get_object_or_404(WarrantyClaim, pk=pk)
    claim.delete()
    messages.success(request, 'Claim deleted.')
    return redirect('claim_list')

@login_required
def claim_export(request):
    claims = WarrantyClaim.objects.all() if request.user.is_superuser else WarrantyClaim.objects.filter(user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="warranty_claims.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID','Job #','Tech','Customer','Date','Amount','Status','Vendor','Submission Method','Confirmation #','Submitted Date','Notes','User'])
    for c in claims:
        writer.writerow([c.id, c.job_number, c.tech_name, c.customer_name, c.claim_date, c.claim_amount, c.get_status_display(), c.vendor, c.vendor_submission_method, c.vendor_confirmation_number, c.vendor_submitted_date, c.notes, c.user.username])
    return response
EOF

cat > apps/home/urls.py << 'EOF'
from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='home'),
    path('claims/', views.claim_list, name='claim_list'),
    path('claims/add/', views.claim_add, name='claim_add'),
    path('claims/<int:pk>/edit/', views.claim_edit, name='claim_edit'),
    path('claims/<int:pk>/delete/', views.claim_delete, name='claim_delete'),
    path('claims/export/', views.claim_export, name='claim_export'),
]
EOF

# --- RMA app (Vendor Parts Returns) ---
cat > apps/rma/models.py << 'EOF'
from django.db import models
from django.contrib.auth.models import User

STATUS_CHOICES = [('NEW','New'),('FILED','Filed'),('PAID','Paid')]

class PartsReturn(models.Model):
    part_number = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    job_number = models.CharField(max_length=50, blank=True, null=True)
    tech_name = models.CharField(max_length=100, blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    return_date = models.DateField(blank=True, null=True)
    vendor = models.CharField(max_length=100, blank=True, null=True)
    rma_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='NEW')
    notes = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parts_returns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"RMA #{self.id} - {self.part_number or 'N/A'} ({self.get_status_display()})"
EOF

cat > apps/rma/forms.py << 'EOF'
from django import forms
from .models import PartsReturn

class PartsReturnForm(forms.ModelForm):
    class Meta:
        model = PartsReturn
        fields = ['part_number','serial_number','description','job_number','tech_name','customer_name','return_date','vendor','rma_number','status','notes']
        widgets = {
            'part_number': forms.TextInput(attrs={'class':'form-control'}),
            'serial_number': forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'job_number': forms.TextInput(attrs={'class':'form-control'}),
            'tech_name': forms.TextInput(attrs={'class':'form-control'}),
            'customer_name': forms.TextInput(attrs={'class':'form-control'}),
            'return_date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'vendor': forms.TextInput(attrs={'class':'form-control'}),
            'rma_number': forms.TextInput(attrs={'class':'form-control'}),
            'status': forms.Select(attrs={'class':'form-control'}),
            'notes': forms.Textarea(attrs={'class':'form-control','rows':3}),
        }
EOF

cat > apps/rma/views.py << 'EOF'
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import PartsReturn
from .forms import PartsReturnForm

@login_required
def parts_return_list(request):
    returns = PartsReturn.objects.all() if request.user.is_superuser else PartsReturn.objects.filter(user=request.user)
    return render(request, 'rma/parts_return_list.html', {'returns': returns})

@login_required
def parts_return_add(request):
    form = PartsReturnForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        rma = form.save(commit=False)
        rma.user = request.user
        rma.save()
        messages.success(request, 'Parts return added successfully!')
        return redirect('parts_return_list')
    return render(request, 'rma/parts_return_form.html', {'form': form, 'title': 'Add Parts Return'})

@login_required
def parts_return_edit(request, pk):
    rma = get_object_or_404(PartsReturn, pk=pk) if request.user.is_superuser else get_object_or_404(PartsReturn, pk=pk, user=request.user)
    form = PartsReturnForm(request.POST or None, instance=rma)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Parts return updated successfully!')
        return redirect('parts_return_list')
    return render(request, 'rma/parts_return_form.html', {'form': form, 'title': 'Edit Parts Return'})

@login_required
def parts_return_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete entries.')
        return redirect('parts_return_list')
    rma = get_object_or_404(PartsReturn, pk=pk)
    rma.delete()
    messages.success(request, 'Parts return deleted.')
    return redirect('parts_return_list')

@login_required
def parts_return_export(request):
    returns = PartsReturn.objects.all() if request.user.is_superuser else PartsReturn.objects.filter(user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="parts_returns.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID','Part #','Serial #','Description','Job #','Tech','Customer','Return Date','Vendor','RMA #','Status','Notes','User'])
    for r in returns:
        writer.writerow([r.id, r.part_number, r.serial_number, r.description, r.job_number, r.tech_name, r.customer_name, r.return_date, r.vendor, r.rma_number, r.get_status_display(), r.notes, r.user.username])
    return response
EOF

cat > apps/rma/urls.py << 'EOF'
from django.urls import path
from . import views
urlpatterns = [
    path('', views.parts_return_list, name='parts_return_list'),
    path('add/', views.parts_return_add, name='parts_return_add'),
    path('<int:pk>/edit/', views.parts_return_edit, name='parts_return_edit'),
    path('<int:pk>/delete/', views.parts_return_delete, name='parts_return_delete'),
    path('export/', views.parts_return_export, name='parts_return_export'),
]
EOF

echo "=== All files written! Now run: source venv/bin/activate && pip install -r requirements.txt && python manage.py makemigrations accounts home rma && python manage.py migrate && python manage.py createsuperuser ==="
