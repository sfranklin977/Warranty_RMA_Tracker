from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('rma/', include('apps.rma.urls')),
    path('', include('apps.home.urls')),
]
