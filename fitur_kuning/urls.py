from django.urls import path
from . import views

app_name = 'fitur_kuning'

urlpatterns = [
    path('venue/', views.venue_list, name='venue_list'),
    path('venue/create/', views.create_venue, name='create_venue'),
    path('venue/<uuid:venue_id>/', views.venue_detail, name='venue_detail'),
    path('venue/<uuid:venue_id>/edit/', views.edit_venue, name='edit_venue'),
    path('venue/<uuid:venue_id>/delete/', views.delete_venue, name='delete_venue'),
    path('event/', views.event_list, name='event_list'),
    path('event/create/', views.create_event, name='create_event'),
    path('event/<uuid:event_id>/get/', views.get_event_for_edit, name='get_event_for_edit'),
    path('event/<uuid:event_id>/edit/', views.edit_event, name='edit_event'),

    path('event/<uuid:event_id>/delete/', views.delete_event, name='delete_event'),
]
