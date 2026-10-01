from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.stand_list_view, name='stand-list'),
    path('stand/<int:pk>/', views.stand_detail_view, name='stand-detail'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    
    # Оновлений логін і кроки 2FA
    path('login/', views.custom_login_view, name='login'),
    path('verify-2fa/', views.verify_2fa_view, name='verify-2fa'),
    path('setup-2fa/', views.setup_2fa_view, name='setup-2fa'),
    
    path('stand/<int:pk>/release/', views.release_stand_view, name='stand-release'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
