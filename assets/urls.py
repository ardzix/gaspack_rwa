from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('assets/', views.AssetListView.as_view(), name='asset_list'),
    path('assets/<uuid:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
] 