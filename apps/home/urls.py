from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('claims/', views.claim_list, name='claim_list'),
    path('claims/add/', views.claim_add, name='claim_add'),
    path('claims/<int:pk>/edit/', views.claim_edit, name='claim_edit'),
    path('claims/<int:pk>/delete/', views.claim_delete, name='claim_delete'),
    path('claims/export/', views.claim_export, name='claim_export'),
    path('claims/sync-servicetitan/', views.claim_sync_servicetitan, name='claim_sync_servicetitan'),
]
