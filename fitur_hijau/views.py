import uuid
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages

# --- HELPER FUNCTIONS ---

def is_logged_in(request):
    """Cek apakah user_id ada di session (tanda sudah login dari folder web)"""
    return 'user_id' in request.session

def get_role(request):
    """Mengambil role name langsung dari session yang di-set saat login"""
    return request.session.get('role', 'guest').lower()

# --- ARTIST LOGIC ---
def list_artist(request):
    """READ: Menampilkan daftar artis dengan statistik sesuai revisi soal"""
    if not is_logged_in(request):
        return redirect('web:login')
        
    role = get_role(request)
    
    with connection.cursor() as cursor:
        # 1. Ambil data utama (Artist ID, Nama, Genre)
        cursor.execute("SELECT artist_id, name, genre FROM tiktaktuk.artist ORDER BY name ASC")
        artis = cursor.fetchall()
        
        # 2. (Opsional) Ambil jumlah genre unik untuk Card Statistik
        cursor.execute("SELECT COUNT(DISTINCT genre) FROM tiktaktuk.artist")
        total_genre = cursor.fetchone()[0]
        
        # 3. (Opsional) Ambil jumlah total artist
        total_artist = len(artis)

    return render(request, 'fitur_hijau/list_artist.html', {
        'artis': artis, 
        'user_role': role, 
        'is_admin': role == 'admin',
        'total_artist': total_artist,
        'total_genre': total_genre,
        'total_event': 6 
    })

def create_artist(request):
    """CREATE: Menambah artis baru (Hanya Admin)"""
    if get_role(request) != 'admin':
        messages.error(request, "Akses ditolak! Cuma Admin yang bisa kelola Artist.")
        return redirect('fitur_hijau:list_artist')

    if request.method == 'POST':
        name = request.POST.get('name')
        genre = request.POST.get('genre')
        artist_id = uuid.uuid4()
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO tiktaktuk.artist (artist_id, name, genre) VALUES (%s, %s, %s)",
                [artist_id, name, genre]
            )
        messages.success(request, f"Artist {name} berhasil ditambahkan!")
        return redirect('fitur_hijau:list_artist')

    return render(request, 'fitur_hijau/form_artist.html', {'mode': 'Tambah'})

def update_artist(request, id):
    if get_role(request) != 'admin':
        messages.error(request, "Akses ditolak! Cuma Admin yang bisa kelola Artist.")
        return redirect('fitur_hijau:list_artist')

    with connection.cursor() as cursor:
        if request.method == 'POST':
            name, genre = request.POST.get('name'), request.POST.get('genre')
            cursor.execute("UPDATE tiktaktuk.artist SET name=%s, genre=%s WHERE artist_id=%s", [name, genre, id])
            messages.success(request, f"Artist {name} berhasil diperbarui!")
            return redirect('fitur_hijau:list_artist')

        cursor.execute("SELECT name, genre FROM tiktaktuk.artist WHERE artist_id = %s", [id])
        data = cursor.fetchone()

    if not data:
        messages.error(request, "Artist tidak ditemukan.")
        return redirect('fitur_hijau:list_artist')

    return render(request, 'fitur_hijau/form_artist.html', {'mode': 'Update', 'data': data})

def delete_artist(request, id):
    """DELETE: Menghapus artis (Hanya Admin)"""
    if get_role(request) != 'admin':
        messages.error(request, "Akses ditolak! Cuma Admin yang bisa kelola Artist.")
        return redirect('fitur_hijau:list_artist')

    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tiktaktuk.artist WHERE artist_id = %s", [id])
        messages.success(request, "Artist berhasil dihapus!")

    return redirect('fitur_hijau:list_artist')

# --- TICKET LOGIC ---

def list_ticket(request):
    """READ: Menampilkan kategori tiket (Semua user yang login)"""
    if not is_logged_in(request):
        return redirect('web:login')

    role = get_role(request)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tc.category_id, tc.category_name, tc.quota, tc.price, e.event_title 
            FROM tiktaktuk.ticket_category tc 
            JOIN tiktaktuk.event e ON tc.tevent_id = e.event_id
            ORDER BY e.event_title ASC, tc.category_name ASC
        """)
        tiket = cursor.fetchall()
    
    return render(request, 'fitur_hijau/list_ticket.html', {
        'tiket': tiket, 
        'user_role': role, 
        'can_manage': role in ['admin', 'organizer'] # Admin & Organizer bisa CUD tiket
    })

def create_ticket(request):
    """CREATE: Menambah kategori tiket (Admin & Organizer)"""
    if get_role(request) not in ['admin', 'organizer']:
        messages.error(request, "Cuma Admin atau Organizer yang bisa kelola Tiket.")
        return redirect('fitur_hijau:list_ticket')

    if request.method == 'POST':
        name = request.POST.get('name')
        quota = request.POST.get('quota')
        price = request.POST.get('price')
        ev_id = request.POST.get('event_id')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tiktaktuk.ticket_category (category_name, quota, price, tevent_id) 
                VALUES (%s, %s, %s, %s)
            """, [name, quota, price, ev_id])
            
        messages.success(request, f"Kategori tiket {name} berhasil dibuat!")
        return redirect('fitur_hijau:list_ticket')
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT event_id, event_title FROM tiktaktuk.event")
        events = cursor.fetchall()
    return render(request, 'fitur_hijau/form_ticket.html', {'events': events, 'mode': 'Tambah'})

def update_ticket(request, id):
    """UPDATE: Mengubah kategori tiket (Admin & Organizer)"""
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
            
            messages.success(request, f"Kategori tiket {name} berhasil diperbarui!")
            return redirect('fitur_hijau:list_ticket')
        
        cursor.execute("SELECT category_name, quota, price, tevent_id FROM tiktaktuk.ticket_category WHERE category_id = %s", [id])
        data = cursor.fetchone()
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
            # Pastiin nama tabel sesuai: ticket_category
            cursor.execute("DELETE FROM tiktaktuk.ticket_category WHERE category_id = %s", [id])
        messages.success(request, "Kategori tiket berhasil dihapus!")
    return redirect('fitur_hijau:list_ticket')