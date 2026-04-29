from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from web.models import AccountRole, Role 

# --- HELPER FUNCTIONS ---

def is_logged_in(request):
    """Cek apakah user_id ada di session (tanda sudah login dari folder web)"""
    return 'user_id' in request.session

def get_role(request):
    """Mengambil role name langsung dari session yang di-set saat login"""
    return request.session.get('role', 'guest').lower()

# --- ARTIST LOGIC ---

def list_artist(request):
    """READ: Menampilkan daftar artis (Bisa diakses semua user yang login)"""
    if not is_logged_in(request):
        return redirect('web:login')
        
    role = get_role(request)
    search = request.GET.get('search', '')
    
    with connection.cursor() as cursor:
        # Query utama dengan search
        query = "SELECT artist_id, name, genre FROM tiktaktuk.artist WHERE 1=1"
        params = []
        
        if search:
            query += " AND (name ILIKE %s OR genre ILIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        query += " ORDER BY name ASC"
        cursor.execute(query, params)
        artis = cursor.fetchall()
        
        # Hitung stats
        cursor.execute("SELECT COUNT(*) FROM tiktaktuk.artist")
        total_artis = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT genre) FROM tiktaktuk.artist")
        total_genre = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT ea.event_id)
            FROM tiktaktuk.artist a
            LEFT JOIN tiktaktuk.event_artist ea ON a.artist_id = ea.artist_id
        """)
        total_event = cursor.fetchone()[0]
    
    return render(request, 'fitur_hijau/list_artist.html', {
        'artis': artis, 
        'user_role': role, 
        'can_manage': role == 'admin',
        'total_artis': total_artis,
        'total_genre': total_genre,
        'total_event': total_event,
        'search': search
    })

def create_artist(request):
    """CREATE: Menambah artis baru (Hanya Admin)"""
    if get_role(request) != 'admin':
        messages.error(request, "Akses ditolak! Cuma Admin yang bisa kelola Artist.")
        return redirect('fitur_hijau:list_artist')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        genre = request.POST.get('genre', '').strip()
        
        if not name or not genre:
            messages.error(request, "Nama dan Genre tidak boleh kosong!")
            return render(request, 'fitur_hijau/form_artist.html', {'mode': 'Tambah'})
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO tiktaktuk.artist (name, genre) VALUES (%s, %s)", [name, genre])
            messages.success(request, f"✅ Artist '{name}' berhasil ditambahkan!")
            return redirect('fitur_hijau:list_artist')
        except Exception as e:
            messages.error(request, f"❌ Error: {str(e)}")
            return render(request, 'fitur_hijau/form_artist.html', {'mode': 'Tambah'})
        
    return render(request, 'fitur_hijau/form_artist.html', {'mode': 'Tambah'})

def update_artist(request, id):
    """UPDATE: Mengubah artis (Hanya Admin)"""
    if get_role(request) != 'admin':
        messages.error(request, "Akses ditolak! Cuma Admin yang bisa edit Artist.")
        return redirect('fitur_hijau:list_artist')

    with connection.cursor() as cursor:
        if request.method == 'POST':
            name = request.POST.get('name', '').strip()
            genre = request.POST.get('genre', '').strip()
            
            if not name or not genre:
                messages.error(request, "Nama dan Genre tidak boleh kosong!")
                cursor.execute("SELECT name, genre FROM tiktaktuk.artist WHERE artist_id = %s", [id])
                data = cursor.fetchone()
                return render(request, 'fitur_hijau/form_artist.html', {'mode': 'Update', 'data': data})
            
            try:
                cursor.execute("UPDATE tiktaktuk.artist SET name=%s, genre=%s WHERE artist_id=%s", [name, genre, id])
                messages.success(request, f"✅ Artist '{name}' berhasil diperbarui!")
                return redirect('fitur_hijau:list_artist')
            except Exception as e:
                messages.error(request, f"❌ Error: {str(e)}")
                cursor.execute("SELECT name, genre FROM tiktaktuk.artist WHERE artist_id = %s", [id])
                data = cursor.fetchone()
                return render(request, 'fitur_hijau/form_artist.html', {'mode': 'Update', 'data': data})
        
        cursor.execute("SELECT name, genre FROM tiktaktuk.artist WHERE artist_id = %s", [id])
        data = cursor.fetchone()
        
        if not data:
            messages.error(request, "Artist tidak ditemukan!")
            return redirect('fitur_hijau:list_artist')
    
    return render(request, 'fitur_hijau/form_artist.html', {'mode': 'Update', 'data': data})

def delete_artist(request, id):
    """DELETE: Menghapus artis (Hanya Admin)"""
    if get_role(request) != 'admin':
        messages.error(request, "❌ Akses ditolak! Cuma Admin yang bisa hapus Artist.")
        return redirect('fitur_hijau:list_artist')
    
    try:
        with connection.cursor() as cursor:
            # Ambil nama artist dulu untuk pesan
            cursor.execute("SELECT name FROM tiktaktuk.artist WHERE artist_id = %s", [id])
            artist_name = cursor.fetchone()
            
            if artist_name:
                cursor.execute("DELETE FROM tiktaktuk.artist WHERE artist_id = %s", [id])
                messages.success(request, f"✅ Artist '{artist_name[0]}' berhasil dihapus!")
            else:
                messages.error(request, "❌ Artist tidak ditemukan!")
    except Exception as e:
        messages.error(request, f"❌ Error: {str(e)}")
    
    return redirect('fitur_hijau:list_artist')

# --- TICKET LOGIC ---

def list_ticket(request):
    """READ: Menampilkan kategori tiket (Semua user yang login)"""
    if not is_logged_in(request):
        return redirect('web:login')

    role = get_role(request)
    search = request.GET.get('search', '')
    event_filter = request.GET.get('event', '')
    
    with connection.cursor() as cursor:
        # Query utama dengan filter
        query = """
            SELECT tc.category_id, tc.category_name, tc.quota, tc.price, e.event_title, e.event_id
            FROM tiktaktuk.ticket_category tc 
            JOIN tiktaktuk.event e ON tc.tevent_id = e.event_id
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND tc.category_name ILIKE %s"
            params.append(f"%{search}%")
        
        if event_filter:
            query += " AND e.event_id = %s"
            params.append(event_filter)
        
        query += " ORDER BY e.event_title ASC, tc.category_name ASC"
        cursor.execute(query, params)
        tiket = cursor.fetchall()
        
        # Hitung statistik
        cursor.execute("""
            SELECT COUNT(*), SUM(quota), MAX(price)
            FROM tiktaktuk.ticket_category
        """)
        stats = cursor.fetchone()
        total_kategori = stats[0] if stats[0] else 0
        total_kuota = stats[1] if stats[1] else 0
        harga_tertinggi = stats[2] if stats[2] else 0
        
        # Ambil list events untuk filter
        cursor.execute("SELECT event_id, event_title FROM tiktaktuk.event ORDER BY event_title")
        events = cursor.fetchall()
    
    return render(request, 'fitur_hijau/list_ticket.html', {
        'tiket': tiket, 
        'user_role': role,
        'events': events,
        'can_manage': role in ['admin', 'organizer'],
        'total_kategori': total_kategori,
        'total_kuota': total_kuota,
        'harga_tertinggi': harga_tertinggi,
        'search': search,
        'event_filter': event_filter
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