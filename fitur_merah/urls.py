from django.urls import path
from . import views

app_name = 'fitur_merah'

urlpatterns = [
    path('seats/', views.list_seat, name='list_seat'),
    path('seats/tambah/', views.create_seat, name='create_seat'),
    path('seats/edit/<uuid:id>/', views.update_seat, name='update_seat'),
    path('seats/hapus/<uuid:id>/', views.delete_seat, name='delete_seat'),
    path('my-tickets/', views.list_ticket, name='list_ticket'),
    path('tickets/tambah/', views.create_ticket, name='create_ticket'),
    path('tickets/edit/<uuid:id>/', views.update_ticket, name='update_ticket'),
    path('tickets/hapus/<uuid:id>/', views.delete_ticket, name='delete_ticket'),
]