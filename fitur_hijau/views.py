from django.shortcuts import render, redirect
from django.db import connection

def get_role(request):
    return request.session.get('user_role', 'guest')

# --- MOCK LOGIN ---
def mock_login(request, role):
    request.session['user_role'] = role
    return redirect('fitur_hijau:list_artist')

# --- artist LOGIC ---
def list_artist(request):
    role = get_role(request)
    with connection.cursor() as cursor:
        # Ganti jadi tiktaktuk.artist
        cursor.execute("SELECT artist_id, name, genre FROM tiktaktuk.artist ORDER BY name ASC")
        artis = cursor.fetchall()
    return render(request, 'fitur_hijau/list_artist.html', {'artis': artis, 'user_role': role, 'is_admin': role == 'admin'})

def create_artist(request):
    if get_role(request) != 'admin': return redirect('fitur_hijau:list_artist')
    if request.method == 'POST':
        name, genre = request.POST.get('name'), request.POST.get('genre')
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO tiktaktuk.artist (name, genre) VALUES (%s, %s)", [name, genre])
        return redirect('fitur_hijau:list_artist')
    return render(request, 'fitur_hijau/form_artist.html', {'mode': 'Tambah'})

def update_artist(request, id):
    if get_role(request) != 'admin': return redirect('fitur_hijau:list_artist')
    with connection.cursor() as cursor:
        if request.method == 'POST':
            name, genre = request.POST.get('name'), request.POST.get('genre')
            cursor.execute("UPDATE tiktaktuk.artist SET name=%s, genre=%s WHERE artist_id=%s", [name, genre, id])
            return redirect('fitur_hijau:list_artist')
        cursor.execute("SELECT name, genre FROM tiktaktuk.artist WHERE artist_id = %s", [id])
        data = cursor.fetchone()
    return render(request, 'fitur_hijau/form_artist.html', {'mode': 'Update', 'data': data})

def delete_artist(request, id):
    if get_role(request) == 'admin':
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tiktaktuk.artist WHERE artist_id = %s", [id])
    return redirect('fitur_hijau:list_artist')

# --- TICKET LOGIC ---
def list_ticket(request):
    role = get_role(request)
    with connection.cursor() as cursor:
        # Ganti EVENT jadi event & tambah tiktaktuk.
        cursor.execute("""
            SELECT tc.category_id, tc.category_name, tc.quota, tc.price, e.event_title 
            FROM tiktaktuk.ticket_category tc JOIN tiktaktuk.event e ON tc.tevent_id = e.event_id
            ORDER BY e.event_title ASC, tc.category_name ASC
        """)
        tiket = cursor.fetchall()
    return render(request, 'fitur_hijau/list_ticket.html', {'tiket': tiket, 'user_role': role, 'can_manage': role in ['admin', 'organizer']})

def create_ticket(request):
    if get_role(request) not in ['admin', 'organizer']: return redirect('fitur_hijau:list_ticket')
    if request.method == 'POST':
        name, quota, price, ev_id = request.POST.get('name'), request.POST.get('quota'), request.POST.get('price'), request.POST.get('event_id')
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO tiktaktuk.ticket_category (category_name, quota, price, tevent_id) VALUES (%s, %s, %s, %s)", [name, quota, price, ev_id])
        return redirect('fitur_hijau:list_ticket')
    with connection.cursor() as cursor:
        # Ganti EVENT jadi event
        cursor.execute("SELECT event_id, event_title FROM tiktaktuk.event")
        events = cursor.fetchall()
    return render(request, 'fitur_hijau/form_ticket.html', {'events': events, 'mode': 'Tambah'})

# --- TICKET LOGIC TAMBAHAN ---
def update_ticket(request, id):
    if get_role(request) not in ['admin', 'organizer']: 
        return redirect('fitur_hijau:list_ticket')
    
    with connection.cursor() as cursor:
        if request.method == 'POST':
            name = request.POST.get('name')
            quota = request.POST.get('quota')
            price = request.POST.get('price')
            ev_id = request.POST.get('event_id')
            
            cursor.execute("""
                UPDATE tiktaktuk.ticket_category 
                SET category_name=%s, quota=%s, price=%s, tevent_id=%s 
                WHERE category_id=%s
            """, [name, quota, price, ev_id, id])
            
            return redirect('fitur_hijau:list_ticket')
        
        cursor.execute("SELECT category_name, quota, price, tevent_id FROM tiktaktuk.ticket_category WHERE category_id = %s", [id])
        data = cursor.fetchone()
        # Ganti EVENT jadi event
        cursor.execute("SELECT event_id, event_title FROM tiktaktuk.event")
        events = cursor.fetchall()
        
    return render(request, 'fitur_hijau/form_ticket.html', {
        'mode': 'Update', 
        'data': data, 
        'events': events,
        'selected_event_id': data[3] if data else None
    })

def delete_ticket(request, id):
    if get_role(request) in ['admin', 'organizer']:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tiktaktuk.ticket_category WHERE category_id = %s", [id])
    return redirect('fitur_hijau:list_ticket')