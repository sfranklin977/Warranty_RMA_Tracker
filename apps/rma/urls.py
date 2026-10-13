from django.urls import path
from . import views

urlpatterns = [
    path('', views.parts_return_list, name='parts_return_list'),
    path('add/', views.parts_return_add, name='parts_return_add'),
    path('import/', views.parts_return_import, name='parts_return_import'),
    path('template/', views.parts_return_template, name='parts_return_template'),
    path('<int:pk>/edit/', views.parts_return_edit, name='parts_return_edit'),
    path('<int:pk>/delete/', views.parts_return_delete, name='parts_return_delete'),
    path('export/', views.parts_return_export, name='parts_return_export'),
]
