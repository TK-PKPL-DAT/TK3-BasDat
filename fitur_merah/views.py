from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
import uuid, random, string

def get_session_data(request):
    user_id = request.session.get('user_id')
    role = 'guest'
    if user_id:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT r.role_name FROM role r 
                JOIN account_role ar ON r.role_id = ar.role_id 
                WHERE ar.user_id = %s
            """, [user_id])
            res = cursor.fetchone()
            if res: 
                role = res[0].lower()
    return role, user_id

# READ SEAT
def list_seat(request):
    role, _ = get_session_data(request)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.seat_id, v.venue_name, s.section, s.row_number, s.seat_number,
                   CASE WHEN hr.ticket_id IS NOT NULL THEN 'Terisi' ELSE 'Tersedia' END as status
            FROM SEAT s
            JOIN VENUE v ON s.venue_id = v.venue_id
            LEFT JOIN HAS_RELATIONSHIP hr ON s.seat_id = hr.seat_id
            ORDER BY v.venue_name, s.section, s.row_number, s.seat_number
        """)
        seats = cursor.fetchall()
    return render(request, 'fitur_merah/list_seat.html', {'seats': seats, 'can_manage': role in ['admin', 'organizer']})

# CREATE SEAT 
def create_seat(request):
    role, _ = get_session_data(request)
    if role not in ['admin', 'organizer']: return redirect('fitur_merah:list_seat')
    
    if request.method == 'POST':
        v_id, sec, row, num = request.POST.get('venue_id'), request.POST.get('section'), request.POST.get('row'), request.POST.get('number')
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO SEAT (seat_id, section, seat_number, row_number, venue_id) VALUES (%s, %s, %s, %s, %s)",
                           [str(uuid.uuid4()), sec, num, row, v_id])
        return redirect('fitur_merah:list_seat')
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT venue_id, venue_name FROM VENUE")
        venues = cursor.fetchall()
    return render(request, 'fitur_merah/form_seat.html', {'venues': venues, 'mode': 'Tambah'})

# DELETE SEAT 
def delete_seat(request, id):
    role, _ = get_session_data(request)
    if role in ['admin', 'organizer']:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM HAS_RELATIONSHIP WHERE seat_id = %s", [str(id)])
            if cursor.fetchone():
                messages.error(request, "Kursi ini sudah di-assign ke tiket dan tidak dapat dihapus.")
            else:
                cursor.execute("DELETE FROM SEAT WHERE seat_id = %s", [str(id)])
    return redirect('fitur_merah:list_seat')

# UPDATE SEAT 
def update_seat(request, id):
    role, _ = get_session_data(request)
    if role not in ['admin', 'organizer']: 
        return redirect('fitur_merah:list_seat')

    with connection.cursor() as cursor:
        if request.method == 'POST':
            v_id = request.POST.get('venue_id')
            sec = request.POST.get('section')
            row = request.POST.get('row')
            num = request.POST.get('number')
            cursor.execute(
                "UPDATE SEAT SET venue_id=%s, section=%s, row_number=%s, seat_number=%s WHERE seat_id=%s",
                [v_id, sec, row, num, str(id)]
            )
            return redirect('fitur_merah:list_seat')
        cursor.execute("SELECT venue_id, section, row_number, seat_number FROM SEAT WHERE seat_id = %s", [str(id)])
        data = cursor.fetchone()
        cursor.execute("SELECT venue_id, venue_name FROM VENUE")
        venues = cursor.fetchall()

    return render(request, 'fitur_merah/form_seat.html', {'data': data, 'venues': venues, 'mode': 'Update'})

# READ TIKET
def list_ticket(request):
    role, u_id = get_session_data(request)
    if role == 'guest':
        messages.warning(request, "Silakan login untuk melihat tiket Anda.")
        return redirect('web:login')
    query = """
        SELECT t.ticket_id, t.ticket_code, c.full_name, e.event_title, tc.category_name, s.seat_number
        FROM TICKET t
        JOIN "ORDER" o ON t.torder_id = o.order_id
        JOIN CUSTOMER c ON o.customer_id = c.customer_id
        JOIN TICKET_CATEGORY tc ON t.tcategory_id = tc.category_id
        JOIN EVENT e ON tc.tevent_id = e.event_id
        LEFT JOIN HAS_RELATIONSHIP hr ON t.ticket_id = hr.ticket_id
        LEFT JOIN SEAT s ON hr.seat_id = s.seat_id
    """
    params = []
    if role == 'customer':
        query += " WHERE c.user_id = %s"
        params.append(u_id)
    elif role == 'organizer':
        query += " WHERE e.organizer_id = (SELECT organizer_id FROM ORGANIZER WHERE user_id = %s)"
        params.append(u_id)
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        tickets = cursor.fetchall()
    return render(request, 'fitur_merah/list_ticket.html', {
        'tickets': tickets, 
        'role': role, 
        'is_admin': role == 'admin'
    })

# CREATE TIKET
def create_ticket(request):
    role, u_id = get_session_data(request)
    if role not in ['admin', 'organizer']: return redirect('fitur_merah:list_ticket')
    if request.method == 'POST':
        ord_id = request.POST.get('order_id')
        cat_id = request.POST.get('category_id')
        seat_id = request.POST.get('seat_id')
        t_id = str(uuid.uuid4())
        t_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO TICKET (ticket_id, ticket_code, tcategory_id, torder_id) VALUES (%s, %s, %s, %s)",
                               [t_id, t_code, cat_id, ord_id])
                if seat_id:
                    cursor.execute("INSERT INTO HAS_RELATIONSHIP (seat_id, ticket_id) VALUES (%s, %s)", [seat_id, t_id])
            messages.success(request, "Tiket berhasil ditambahkan!")
        except Exception as e:
            messages.error(request, f"Gagal menambahkan tiket: {e}")
        return redirect('fitur_merah:list_ticket')
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT o.order_id, c.full_name FROM "ORDER" o 
            JOIN CUSTOMER c ON o.customer_id = c.customer_id
        """)
        orders = cursor.fetchall()
        cursor.execute("""
            SELECT tc.category_id, tc.category_name, tc.price, e.event_title 
            FROM TICKET_CATEGORY tc 
            JOIN EVENT e ON tc.tevent_id = e.event_id
        """)
        categories = cursor.fetchall()

        cursor.execute("""
            SELECT s.seat_id, s.section, s.row_number, s.seat_number 
            FROM SEAT s 
            LEFT JOIN HAS_RELATIONSHIP hr ON s.seat_id = hr.seat_id 
            WHERE hr.ticket_id IS NULL
        """)
        seats = cursor.fetchall()
    return render(request, 'fitur_merah/form_ticket.html', {
        'mode': 'Tambah',
        'orders': orders,
        'categories': categories,
        'seats': seats
    })

# DELETE TIKET
def delete_ticket(request, id):
    role, _ = get_session_data(request)
    if role == 'admin':
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM HAS_RELATIONSHIP WHERE ticket_id = %s", [str(id)])
            cursor.execute("DELETE FROM TICKET WHERE ticket_id = %s", [str(id)])
    return redirect('fitur_merah:list_ticket')

# UPDATE TIKET
def update_ticket(request, id):
    role, _ = get_session_data(request)
    if role != 'admin': 
        return redirect('fitur_merah:list_ticket')

    if request.method == 'POST':
        new_seat_id = request.POST.get('seat_id')
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM HAS_RELATIONSHIP WHERE ticket_id = %s", [str(id)])

            if new_seat_id:
                cursor.execute("INSERT INTO HAS_RELATIONSHIP (seat_id, ticket_id) VALUES (%s, %s)", [new_seat_id, str(id)])
        return redirect('fitur_merah:list_ticket')
    
    return render(request, 'fitur_merah/form_ticket.html', {'mode': 'Update'})

# Dashboard laporan
def report_dashboard(request):
    context = {
        'page_title': 'Dashboard Laporan'
    }
    return render(request, 'fitur_merah/report_dashboard.html', context)
