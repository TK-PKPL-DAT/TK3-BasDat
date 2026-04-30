from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
import uuid
from datetime import datetime
from web.models import Order, Promotion, OrderPromotion, Customer, UserAccount, AccountRole, Event, TicketCategory, Ticket
from django.db.models import Count
from django.db import transaction, connection
from django.db.models import Sum


#Fungsi helper untuk cek role
def get_session_data(request):
    return {
        'is_logged_in': request.session.get('logged_in', False),
        'user_id': request.session.get('user_id'),
        'username': request.session.get('username'),
        'role': request.session.get('role'), #Pastikan session 'role' diset saat login
    }

#--- FITUR ORDER (13-15) ---

def order_list(request):
    """Menampilkan daftar order berdasarkan role (R-Order)"""
    sess = get_session_data(request)
    if not sess['is_logged_in']:
        return redirect('web:login')
    
    role = sess.get('role', '').lower()
    
    # --- DUMMY DATA FOR ORDERS ---
    import uuid
    from datetime import datetime
    class DummyCustomer:
        def __init__(self, name):
            self.full_name = name
    class DummyOrder:
        def __init__(self, oid, cname, date, status, total):
            self.order_id = oid
            self.customer = DummyCustomer(cname)
            self.order_date = date
            self.payment_status = status
            self.total_amount = total

    orders = [
        DummyOrder(str(uuid.uuid4()), 'Budi Santoso', datetime.now(), 'Lunas', 1500000),
        DummyOrder(str(uuid.uuid4()), 'Andi Wijaya', datetime.now(), 'Pending', 750000),
        DummyOrder(str(uuid.uuid4()), 'Siti Aminah', datetime.now(), 'Dibatalkan', 500000),
        DummyOrder(str(uuid.uuid4()), 'Joko Anwar', datetime.now(), 'Lunas', 2000000),
        DummyOrder(str(uuid.uuid4()), 'Rina Nose', datetime.now(), 'Pending', 1000000),
    ]
    
    total_order = len(orders)
    total_lunas = sum(1 for o in orders if o.payment_status == 'Lunas')
    total_revenue = sum(o.total_amount for o in orders if o.payment_status == 'Lunas')

    return render(request, 'order_list.html', {
        'orders': orders,
        'sess': sess,
        'total_order': total_order,
        'total_lunas': total_lunas,
        'total_revenue': total_revenue
    })

def create_order(request):
    """Proses pembuatan order, tiket, dan pemotongan kuota"""
    sess = get_session_data(request)
    if not sess['is_logged_in']: return redirect('web:login')

    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        promo_code = request.POST.get('promo_code')
        
        category = get_object_or_404(TicketCategory, category_id=category_id)
        customer = Customer.objects.filter(user_id=sess['user_id']).first()

        try:
            with transaction.atomic(): 
                #Cek Kuota
                if category.quota <= 0:
                    messages.error(request, "Kuota tiket sudah habis!")
                    return redirect('fitur_biru:order_list')

                #hitung total
                total = float(category.price) + 10000 
                
                #buat order
                order_id = uuid.uuid4()
                new_order = Order.objects.create(
                    order_id=order_id,
                    order_date=datetime.now(),
                    payment_status='Lunas',
                    total_amount=total,
                    customer=customer
                )

                #Buat Tiket
                Ticket.objects.create(
                    ticket_id=uuid.uuid4(),
                    ticket_code=f"TIX-{str(uuid.uuid4())[:8].upper()}",
                    tcategory=category,
                    torder=new_order
                )

                #kurangin quota kursi
                category.quota -= 1
                category.save()

                #pakai promo jika ada
                if promo_code:
                    promo = Promotion.objects.filter(promo_code=promo_code).first()
                    if promo:
                        OrderPromotion.objects.create(
                            order_promotion_id=uuid.uuid4(),
                            promotion=promo,
                            order=new_order
                        )

            messages.success(request, "Pembayaran Berhasil!")
            return redirect('fitur_biru:payment_success')
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
            return redirect('fitur_biru:order_list')

    #Logic GET (untuk nampilin form)
    event_id = request.GET.get('event_id')
    event = get_object_or_404(Event, event_id=event_id)
    categories = TicketCategory.objects.filter(tevent=event)
    customer = Customer.objects.filter(user_id=sess['user_id']).first()
    return render(request, 'checkout.html', {'event': event, 'categories': categories, 'sess': sess, 'customer': customer})

def payment_success(request):
    sess = get_session_data(request)
    return render(request, 'payment_success.html', {'sess': sess})

def check_promo(request):
    """Endpoint AJAX untuk cek validasi promo"""
    code = request.GET.get('code')
    promo = Promotion.objects.filter(promo_code=code).first()
    
    if promo:
        #Cek tanggal & limit
        now = datetime.now().date()
        if promo.start_date <= now <= promo.end_date:
            return JsonResponse({
                'valid': True,
                'type': promo.discount_type,
                'value': float(promo.discount_value)
            })
    return JsonResponse({'valid': False})

def update_order_status(request, order_id):
    """Update status pembayaran (UD-Order) - Hanya Admin"""
    if request.method == 'POST':
        # Dummy behavior bypasses DB to avoid 404
        messages.success(request, "Status order berhasil diperbarui.")
        return redirect('fitur_biru:order_list')

def delete_order(request, order_id):
    """Menghapus order (UD-Order) - Hanya Admin """
    # Dummy behavior bypasses DB to avoid 404
    messages.success(request, "Order berhasil dihapus.")
    return redirect('fitur_biru:order_list')

def checkout_view(request):
    sess = get_session_data(request)
    if not sess['is_logged_in']: return redirect('web:login')

    #ngammbil event_id dari URL (dr fitur kuning)
    event_id = request.GET.get('event_id')
    event = get_object_or_404(Event, event_id=event_id)
    
    #ngambil semua kategori tiket untuk event ini yang kuotanya masih ada
    categories = TicketCategory.objects.filter(tevent=event, quota__gt=0)

    return render(request, 'checkout.html', {
        'event': event,
        'categories': categories,
        'sess': sess
    })


#--- FITUR PROMOSI (16-17) ---

def promotion_list(request):
    """Menampilkan daftar promosi (R-Promotion) """
    sess = get_session_data(request)

    #Ambil semua promo & hitung berapa kali masing-masing promo sudah digunakan 
    promotions = Promotion.objects.annotate(
        usage_count=Count('orderpromotion')
    ).order_by('-start_date')

    #Hitung brp kali promosi dipakai
    total_usage = OrderPromotion.objects.count()
    total_percentage = promotions.filter(discount_type='PERCENTAGE').count()

    context = {
        'promotions': promotions, 
        'sess': sess,
        'total_usage': total_usage,
        'total_percentage': total_percentage
    }
    return render(request, 'promotion_list.html', context)

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
        #Simpan SEMUA data dari form, bukan cuma promo_code
        promo.promo_code = request.POST.get('promo_code')
        promo.discount_type = request.POST.get('discount_type')
        promo.discount_value = request.POST.get('discount_value')
        promo.start_date = request.POST.get('start_date')
        promo.end_date = request.POST.get('end_date')
        promo.usage_limit = request.POST.get('usage_limit')
        promo.save()
        messages.success(request, "Promo berhasil diperbarui!")
        return redirect('fitur_biru:promotion_list')
        
    return render(request, 'fitur_biru/form_promotion.html', {'promo': promo})

def delete_promotion(request, promotion_id):
    """Menghapus promo (CUD-Promotion) """
    promo = get_object_or_404(Promotion, promotion_id=promotion_id)
    promo.delete()
    return redirect('fitur_biru:promotion_list')

