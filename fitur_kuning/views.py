from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count, Min
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import connection  # <-- Ditambahkan untuk query raw SQL
import uuid
# <-- EventArtist dihapus dari import list di bawah
from web.models import Venue, Seat, UserAccount, AccountRole, Event, TicketCategory, Organizer, Artist
from .forms import VenueSearchForm, CreateVenueForm


def is_admin_or_organizer(request):
    """Check if user is admin or organizer"""
    if not request.session.get('logged_in'):
        return False
    
    try:
        user_id = request.session.get('user_id')
        account_role = AccountRole.objects.filter(user_id=user_id).first()
        if account_role and account_role.role:
            return account_role.role.role_name in ['admin', 'organizer']
    except:
        pass
    
    return False


def get_user_role(request):
    """Get user role"""
    if not request.session.get('logged_in'):
        return None
    
    try:
        user_id = request.session.get('user_id')
        account_role = AccountRole.objects.filter(user_id=user_id).first()
        if account_role and account_role.role:
            return account_role.role.role_name
    except:
        pass
    
    return None


def venue_list(request):
    """Menampilkan daftar venue dengan search dan filter"""
    
    # Query semua venue
    venues = Venue.objects.all()
    
    # Get statistics
    total_venues = venues.count()
    reserved_seating = Seat.objects.filter(section__icontains='reserved').count()
    total_capacity = sum([v.capacity for v in venues])
    
    # Form search dan filter
    form = VenueSearchForm(request.GET or None)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        venues = venues.filter(
            Q(venue_name__icontains=search_query) | 
            Q(address__icontains=search_query)
        )
    
    # Filter by city
    city_filter = request.GET.get('city', '')
    if city_filter:
        venues = venues.filter(city=city_filter)
    
    # Filter by seating type (melalui Seat)
    seating_filter = request.GET.get('seating_type', '')
    if seating_filter:
        venue_ids = Seat.objects.filter(section__icontains=seating_filter).values_list('venue_id', flat=True)
        venues = venues.filter(venue_id__in=venue_ids)
    
    # Add seating_type for each venue
    for venue in venues:
        has_reserved = Seat.objects.filter(venue_id=venue.venue_id, section__icontains='reserved').exists()
        venue.seating_type = 'RESERVED SEATING' if has_reserved else 'FREE SEATING'
    
    # Check user role
    is_admin_or_org = is_admin_or_organizer(request)
    user_role = get_user_role(request)
    is_logged_in = request.session.get('logged_in', False)
    
    # Get unique cities dan seating types untuk dropdown
    all_cities = Venue.objects.values_list('city', flat=True).distinct().order_by('city')
    all_seating_types = Seat.objects.values_list('section', flat=True).distinct().order_by('section')
    
    context = {
        'venues': venues,
        'form': form,
        'total_venues': total_venues,
        'reserved_seating': reserved_seating,
        'total_capacity': total_capacity,
        'is_admin_or_organizer': is_admin_or_org,
        'user_role': user_role,
        'is_logged_in': is_logged_in,
        'search_query': search_query,
        'city_filter': city_filter,
        'seating_filter': seating_filter,
        'all_cities': all_cities,
        'all_seating_types': all_seating_types,
    }
    
    return render(request, 'fitur_kuning/venue_list.html', context)


def venue_detail(request, venue_id):
    """Menampilkan detail venue"""
    venue = get_object_or_404(Venue, venue_id=venue_id)
    
    # Get seats untuk venue ini
    seats = Seat.objects.filter(venue_id=venue_id)
    
    # Count seats by section
    seats_by_section = {}
    for seat in seats:
        if seat.section not in seats_by_section:
            seats_by_section[seat.section] = []
        seats_by_section[seat.section].append(seat)
    
    context = {
        'venue': venue,
        'seats_by_section': seats_by_section,
        'is_admin_or_organizer': is_admin_or_organizer(request),
    }
    
    return render(request, 'fitur_kuning/venue_detail.html', context)


@require_http_methods(["GET", "POST"])
def create_venue(request):
    """Membuat venue baru untuk admin dan organizer"""
    
    # Check if user is admin or organizer
    if not is_admin_or_organizer(request):
        messages.error(request, 'Hanya admin dan organizer yang bisa membuat venue!')
        return redirect('fitur_kuning:venue_list')
    
    if request.method == 'POST':
        form = CreateVenueForm(request.POST)
        if form.is_valid():
            try:
                # Create new venue
                venue = Venue(
                    venue_id=uuid.uuid4(),
                    venue_name=form.cleaned_data['venue_name'],
                    capacity=form.cleaned_data['capacity'],
                    address=form.cleaned_data['address'],
                    city=form.cleaned_data['city'],
                )
                venue.save()
                
                # Create default seats based on seating type
                has_reserved = form.cleaned_data.get('has_reserved_seating', False)
                seating_section = 'RESERVED' if has_reserved else 'FREE'
                
                # Create default seat entries using bulk_create for better performance
                capacity = int(form.cleaned_data['capacity'])
                seats_to_create = []
                
                for i in range(1, capacity + 1):
                    row = chr(65 + (i - 1) // 20)  # A, B, C, D, E... berdasarkan 20 kursi per baris
                    seat_num = (i - 1) % 20 + 1
                    
                    seats_to_create.append(
                        Seat(
                            seat_id=uuid.uuid4(),
                            section=seating_section,
                            seat_number=str(seat_num),
                            row_number=row,
                            venue_id=venue.venue_id
                        )
                    )
                
                # Bulk create seats for better performance
                Seat.objects.bulk_create(seats_to_create)
                
                messages.success(request, f"Venue '{venue.venue_name}' berhasil dibuat dengan tipe seating: {seating_section}!")
                return redirect('fitur_kuning:venue_list')
            except Exception as e:
                messages.error(request, f'Gagal membuat venue: {str(e)}')
                return redirect('fitur_kuning:venue_list')
        else:
            # If form is invalid, return with errors
            context = {
                'form': form,
                'has_errors': True,
                'form_errors': form.errors,
            }
            return render(request, 'fitur_kuning/venue_list.html', context)
    
    else:  # GET request
        form = CreateVenueForm()
        context = {
            'form': form,
            'create_venue_modal': True,
        }
        return render(request, 'fitur_kuning/venue_list.html', context)


@require_http_methods(["GET", "POST"])
def edit_venue(request, venue_id):
    """Edit venue untuk admin dan organizer"""
    
    # Check if user is admin or organizer
    if not is_admin_or_organizer(request):
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    venue = get_object_or_404(Venue, venue_id=venue_id)
    
    if request.method == 'POST':
        form = CreateVenueForm(request.POST, instance=venue)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"Venue '{venue.venue_name}' berhasil diperbarui!")
                return redirect('fitur_kuning:venue_list')
            except Exception as e:
                messages.error(request, f'Gagal memperbarui venue: {str(e)}')
                return redirect('fitur_kuning:venue_list')
        else:
            context = {
                'form': form,
                'has_errors': True,
                'form_errors': form.errors,
                'edit_mode': True,
                'venue_id': venue_id,
            }
            return render(request, 'fitur_kuning/venue_list.html', context)
    
    else:  # GET request
        form = CreateVenueForm(instance=venue)
        return JsonResponse({
            'success': True,
            'venue': {
                'venue_id': str(venue.venue_id),
                'venue_name': venue.venue_name,
                'capacity': venue.capacity,
                'city': venue.city,
                'address': venue.address,
            }
        })


@require_http_methods(["POST"])
def delete_venue(request, venue_id):
    """Delete venue untuk admin dan organizer"""
    
    # Check if user is admin or organizer
    if not is_admin_or_organizer(request):
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        venue = get_object_or_404(Venue, venue_id=venue_id)
        venue_name = venue.venue_name
        venue.delete()
        messages.success(request, f"Venue '{venue_name}' berhasil dihapus!")
        return redirect('fitur_kuning:venue_list')
    except Exception as e:
        messages.error(request, f'Gagal menghapus venue: {str(e)}')
        return redirect('fitur_kuning:venue_list')


def event_list(request):
    """Menampilkan daftar semua event dengan search dan filter"""
    
    events = Event.objects.all().select_related('venue', 'organizer')
    is_admin_or_org = is_admin_or_organizer(request)
    user_role = get_user_role(request)
    is_logged_in = request.session.get('logged_in', False)
    
    # Search by event title or artist
    search_query = request.GET.get('search', '')
    if search_query:
        # RAW SQL: Cari event_id berdasarkan nama artis yang di search
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ea.event_id FROM event_artist ea
                JOIN artist a ON ea.artist_id = a.artist_id
                WHERE a.name ILIKE %s
            """, [f'%{search_query}%'])
            artist_event_ids = [row[0] for row in cursor.fetchall()]

        events = events.filter(
            Q(event_title__icontains=search_query) |
            Q(event_id__in=artist_event_ids)
        ).distinct()
    
    # Filter by venue
    venue_filter = request.GET.get('venue', '')
    if venue_filter:
        events = events.filter(venue_id=venue_filter)
    
    # Filter by artist
    artist_filter = request.GET.get('artist', '')
    if artist_filter:
        with connection.cursor() as cursor:
            cursor.execute("SELECT event_id FROM event_artist WHERE artist_id = %s", [artist_filter])
            artist_event_ids = [row[0] for row in cursor.fetchall()]
        events = events.filter(event_id__in=artist_event_ids).distinct()
    
    all_venues = Venue.objects.all().order_by('venue_name')
    all_artists = Artist.objects.all().order_by('name')
    
    events_data = []
    for event in events:
        # RAW SQL: Ambil daftar artis untuk event ini
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT a.artist_id, a.name, a.genre 
                FROM artist a 
                JOIN event_artist ea ON a.artist_id = ea.artist_id 
                WHERE ea.event_id = %s
            """, [str(event.event_id)])
            artists_list = [Artist(artist_id=row[0], name=row[1], genre=row[2]) for row in cursor.fetchall()]
        
        # Get ticket categories untuk event ini
        ticket_categories = TicketCategory.objects.filter(tevent=event)
        min_price = ticket_categories.aggregate(Min('price'))['price__min'] if ticket_categories.exists() else 0
        
        events_data.append({
            'event': event,
            'artists': artists_list,
            'categories': ticket_categories,
            'min_price': min_price,
        })
    
    context = {
        'events_data': events_data,
        'all_venues': all_venues,
        'all_artists': all_artists,
        'is_admin_or_organizer': is_admin_or_org,
        'user_role': user_role,
        'is_logged_in': is_logged_in,
        'search_query': search_query,
        'venue_filter': venue_filter,
        'artist_filter': artist_filter,
    }
    
    return render(request, 'fitur_kuning/event_list.html', context)





@require_http_methods(["POST"])
def create_event(request):
    """Membuat event baru untuk admin dan organizer"""
    if not is_admin_or_organizer(request):
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        import json
        from datetime import datetime
        
        data = json.loads(request.body)
        
        if not data.get('event_title'):
            return JsonResponse({'success': False, 'message': 'Judul acara harus diisi'}, status=400)
        if not data.get('event_date'):
            return JsonResponse({'success': False, 'message': 'Tanggal acara harus diisi'}, status=400)
        if not data.get('event_time'):
            return JsonResponse({'success': False, 'message': 'Waktu acara harus diisi'}, status=400)
        if not data.get('venue_id'):
            return JsonResponse({'success': False, 'message': 'Venue harus dipilih'}, status=400)
        
        event_datetime_str = f"{data['event_date']} {data['event_time']}"
        event_datetime = datetime.strptime(event_datetime_str, '%m/%d/%Y %H:%M')
        
        user_id = request.session.get('user_id')
        user_role = get_user_role(request)
        
        # Untuk admin, buat/ambil organizer default. Untuk organizer, ambil dari DB
        if user_role == 'admin':
            organizer, _ = Organizer.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'organizer_id': uuid.uuid4(),
                    'organizer_name': 'Admin Organizer',
                    'contact_email': 'admin@tiktaktuk.com'
                }
            )
        else:
            organizer = Organizer.objects.filter(user_id=user_id).first()
            if not organizer:
                return JsonResponse({'success': False, 'message': 'Organizer tidak ditemukan'}, status=400)
        
        venue = get_object_or_404(Venue, venue_id=data['venue_id'])
        event = Event(
            event_id=uuid.uuid4(),
            event_title=data['event_title'],
            event_datetime=event_datetime,
            venue=venue,
            organizer=organizer,
        )
        event.save()
        
        # RAW SQL: Insert artist event
        if data.get('artists'):
            with connection.cursor() as cursor:
                for artist_id in data['artists']:
                    artist = Artist.objects.filter(artist_id=artist_id).first()
                    if artist:
                        cursor.execute(
                            "INSERT INTO event_artist (event_id, artist_id) VALUES (%s, %s)",
                            [str(event.event_id), str(artist.artist_id)]
                        )
        
        if data.get('ticket_categories'):
            for cat_data in data['ticket_categories']:
                price = float(cat_data.get('price', 0))
                quota = int(cat_data.get('quota', 0))
                TicketCategory.objects.create(
                    category_id=uuid.uuid4(),
                    category_name=cat_data.get('name', 'Unnamed'),
                    price=price,
                    quota=quota,
                    tevent=event,
                )
        
        return JsonResponse({
            'success': True,
            'message': f"Event '{event.event_title}' berhasil dibuat!",
            'event_id': str(event.event_id)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)


@require_http_methods(["GET"])
def get_event_for_edit(request, event_id):
    """Get event data for edit modal (JSON response)"""
    if not is_admin_or_organizer(request):
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        event = get_object_or_404(Event, event_id=event_id)
        event_date = event.event_datetime.strftime('%Y-%m-%d')
        event_time = event.event_datetime.strftime('%H:%M')
        
        # RAW SQL: Ambil daftar artist ID
        with connection.cursor() as cursor:
            cursor.execute("SELECT artist_id FROM event_artist WHERE event_id = %s", [str(event.event_id)])
            artists = [str(row[0]) for row in cursor.fetchall()]
        
        ticket_categories = TicketCategory.objects.filter(tevent=event)
        categories = [{
                'name': cat.category_name,
                'price': str(cat.price),
                'quota': str(cat.quota),
                'id': str(cat.category_id),
            } for cat in ticket_categories]
        
        data = {
            'success': True,
            'event': {
                'event_id': str(event.event_id),
                'event_title': event.event_title,
                'event_date': event_date,
                'event_time': event_time,
                'venue_id': str(event.venue.venue_id),
            },
            'artists': artists,
            'categories': categories,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)


@require_http_methods(["POST"])
def edit_event(request, event_id):
    """Edit event untuk admin dan organizer"""
    if not is_admin_or_organizer(request):
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        import json
        from datetime import datetime
        
        event = get_object_or_404(Event, event_id=event_id)
        data = json.loads(request.body)
        
        if data.get('event_title'):
            event.event_title = data['event_title']
        
        if data.get('event_date') and data.get('event_time'):
            event_datetime_str = f"{data['event_date']} {data['event_time']}"
            event.event_datetime = datetime.strptime(event_datetime_str, '%m/%d/%Y %H:%M')
        
        if data.get('venue_id'):
            venue = get_object_or_404(Venue, venue_id=data['venue_id'])
            event.venue = venue
        
        event.save()
        
        # RAW SQL: Update artists
        if 'artists' in data:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM event_artist WHERE event_id = %s", [str(event.event_id)])
                for artist_id in data['artists']:
                    artist = Artist.objects.filter(artist_id=artist_id).first()
                    if artist:
                        cursor.execute(
                            "INSERT INTO event_artist (event_id, artist_id) VALUES (%s, %s)",
                            [str(event.event_id), str(artist.artist_id)]
                        )
        
        if 'ticket_categories' in data:
            TicketCategory.objects.filter(tevent=event).delete()
            for cat_data in data['ticket_categories']:
                price = float(cat_data.get('price', 0))
                quota = int(cat_data.get('quota', 0))
                TicketCategory.objects.create(
                    category_id=uuid.uuid4(),
                    category_name=cat_data.get('name', 'Unnamed'),
                    price=price,
                    quota=quota,
                    tevent=event,
                )
        
        return JsonResponse({
            'success': True,
            'message': f"Event '{event.event_title}' berhasil diperbarui!"
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)


@require_http_methods(["POST"])
def delete_event(request, event_id):
    """Delete event untuk admin dan organizer"""
    if not is_admin_or_organizer(request):
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        event = get_object_or_404(Event, event_id=event_id)
        
        # Hapus relasi artist terlebih dahulu
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM event_artist WHERE event_id = %s", [str(event.event_id)])
            
        event.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Event berhasil dihapus!'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)