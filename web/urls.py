from django.urls import path
from . import views

app_name = 'web'
urlpatterns = [
    path('', views.register_view, name='register'),
    path('register/form/', views.register_form_view, name='register_form'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
