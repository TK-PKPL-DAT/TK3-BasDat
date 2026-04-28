from django.urls import path
from . import views

app_name = 'fitur_biru'

urlpatterns = [
    # Fitur Order
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/update/<uuid:order_id>/', views.update_order_status, name='update_order_status'),
    path('orders/delete/<uuid:order_id>/', views.delete_order, name='delete_order'),
    path('payment-success/', views.payment_success, name='payment_success'),
    
    # Fitur Promosi
    path('promotions/', views.promotion_list, name='promotion_list'),
    path('promotions/create/', views.create_promotion, name='create_promotion'),
    path('promotions/edit/<uuid:promotion_id>/', views.edit_promotion, name='edit_promotion'),
    path('promotions/delete/<uuid:promotion_id>/', views.delete_promotion, name='delete_promotion'),
    
    #cek promo
    path('check-promo/', views.check_promo, name='check_promo'),
]