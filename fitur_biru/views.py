from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
import uuid
from datetime import datetime
from web.models import Order, Promotion, OrderPromotion, Customer, UserAccount, AccountRole

# Fungsi helper untuk cek role
def get_session_data(request):
    return {
        'is_logged_in': request.session.get('logged_in', False),
        'user_id': request.session.get('user_id'),
        'username': request.session.get('username'),
        'role': request.session.get('role'), # Pastikan session 'role' diset saat login
    }

# --- FITUR ORDER (13-15) ---

def order_list(request):
    """Menampilkan daftar order berdasarkan role (R-Order)"""
    sess = get_session_data(request)
    if not sess['is_logged_in']:
        return redirect('web:login')

    # filter Role
    if sess['role'] == 'admin':
        # Admin melihat semua order 
        orders = Order.objects.all().order_by('-order_date')
        
    elif sess['role'] == 'organizer':
        # Organizer melihat order terkait eventnya (Filtered by Id)
        # pakai Raw SQL agar lebih simpel untuk join
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT o.* FROM "ORDER" o
                JOIN ticket t ON o.order_id = t.torder_id
                JOIN ticket_category tc ON t.tcategory_id = tc.category_id
                JOIN event e ON tc.tevent_id = e.event_id
                JOIN organizer org ON e.organizer_id = org.organizer_id
                WHERE org.user_id = %s
                ORDER BY o.order_date DESC
            """, [sess['user_id']])
            orders = cursor.fetchall() 
    else:
        # Customer melihat order miliknya sendiri
        customer = Customer.objects.filter(user_id=sess['user_id']).first()
        orders = Order.objects.filter(customer=customer).order_by('-order_date')

    return render(request, 'order_list.html', {'orders': orders, 'sess': sess})

def create_order(request):
    """Membuat pesanan baru (C-Order) - Hanya Customer"""
    if request.method == 'POST':
        sess = get_session_data(request)
        customer = Customer.objects.filter(user_id=sess['user_id']).first()
        
        # (13) Buat record order baru dengan status Pending
        new_order = Order.objects.create(
            order_id=uuid.uuid4(),
            order_date=datetime.now(),
            payment_status='Pending',
            total_amount=request.POST.get('total_amount', 0),
            customer=customer
        )
        messages.success(request, "Pesanan berhasil dibuat!")
        return redirect('fitur_biru:order_list')
    return render(request, 'checkout.html')

def update_order_status(request, order_id):
    """Update status pembayaran (UD-Order) - Hanya Admin"""
    if request.method == 'POST':
        order = get_object_or_404(Order, order_id=order_id)
        order.payment_status = request.POST.get('status') # Lunas/Batal [cite: 1317]
        order.save()
        return JsonResponse({'success': True})

def delete_order(request, order_id):
    """Menghapus order (UD-Order) - Hanya Admin """
    order = get_object_or_404(Order, order_id=order_id)
    order.delete()
    messages.success(request, "Order berhasil dihapus.")
    return redirect('fitur_biru:order_list')


# --- FITUR PROMOSI (16-17) ---

def promotion_list(request):
    """Menampilkan daftar promosi (R-Promotion) """
    promotions = Promotion.objects.all().order_by('-start_date')
    sess = get_session_data(request)
    return render(request, 'promotion_list.html', {'promotions': promotions, 'sess': sess})

def create_promotion(request):
    """Membuat promo baru (CUD-Promotion) - Hanya Admin """
    if request.method == 'POST':
        Promotion.objects.create(
            promotion_id=uuid.uuid4(),
            promo_code=request.POST.get('promo_code'),
            discount_type=request.POST.get('discount_type'),
            discount_value=request.POST.get('discount_value'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            usage_limit=request.POST.get('usage_limit')
        )
        messages.success(request, "Promo berhasil dibuat!")
        return redirect('fitur_biru:promotion_list')
    return render(request, 'form_promotion.html')

def edit_promotion(request, promotion_id):
    """Mengubah promo (CUD-Promotion) """
    promo = get_object_or_404(Promotion, promotion_id=promotion_id)
    if request.method == 'POST':
        promo.promo_code = request.POST.get('promo_code')
        promo.save()
        return redirect('fitur_biru:promotion_list')
    return render(request, 'fitur_biru/form_promotion.html', {'promo': promo})

def delete_promotion(request, promotion_id):
    """Menghapus promo (CUD-Promotion) """
    promo = get_object_or_404(Promotion, promotion_id=promotion_id)
    promo.delete()
    return redirect('fitur_biru:promotion_list')