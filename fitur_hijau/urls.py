from django.urls import path
from . import views

app_name = 'fitur_hijau'

urlpatterns = [
    path('artist/', views.list_artist, name='list_artist'),
    path('artist/tambah/', views.create_artist, name='create_artist'),
    path('artist/edit/<uuid:id>/', views.update_artist, name='update_artist'),
    path('artist/hapus/<uuid:id>/', views.delete_artist, name='delete_artist'),
    path('ticket/', views.list_ticket, name='list_ticket'),
    path('ticket/tambah/', views.create_ticket, name='create_ticket'),
    path('ticket-category/update/<uuid:id>/', views.update_ticket, name='update_ticket'),
    path('ticket-category/delete/<uuid:id>/', views.delete_ticket, name='delete_ticket'),
]