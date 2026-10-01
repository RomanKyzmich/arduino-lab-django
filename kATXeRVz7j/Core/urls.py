from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    # Це буде головна сторінка сайту
    path('', views.stand_list_view, name='stand-list'),
    path('stand/<int:pk>/', views.stand_detail_view, name='stand-detail'),
    # Наша нова сторінка реєстрації
    path('signup/', views.SignUpView.as_view(), name='signup'),

    # Вбудований View для входу
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),

    path('stand/<int:pk>/release/', views.release_stand_view, name='stand-release'),

    # Вбудований View для виходу
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

]