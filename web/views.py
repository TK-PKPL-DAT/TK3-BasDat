from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserAccount, Role, Customer, Organizer, AccountRole
from .forms import CustomerRegisterForm, OrganizerRegisterForm, AdminRegisterForm, LoginForm
import uuid


def test_db_view(request):
    # Mengambil semua data dari tabel USER_ACCOUNT
    data_user = UserAccount.objects.all()
    return render(request, 'test_db.html', {'users': data_user})


def register_view(request):
    """Halaman pilihan role untuk registrasi"""
    return render(request, 'role_selection.html')


def register_form_view(request):
    """Halaman form registrasi berdasarkan role yang dipilih"""
    role = request.GET.get('role', '').lower()
    
    # Validasi role
    valid_roles = ['customer', 'organizer', 'admin']
    if role not in valid_roles:
        messages.error(request, 'Role tidak valid!')
        return redirect('register')
    
    # Tentukan form dan informasi role
    role_info = {
        'customer': {
            'title': 'Pelanggan',
            'icon': '👤',
            'description': 'Beli dan kelola tiket untuk acara favorit Anda',
            'form_class': CustomerRegisterForm
        },
        'organizer': {
            'title': 'Penyelenggara',
            'icon': '🎪',
            'description': 'Buat dan kelola acara serta venue Anda',
            'form_class': OrganizerRegisterForm
        },
        'admin': {
            'title': 'Admin',
            'icon': '⚙️',
            'description': 'Kelola sistem dan pengguna platform',
            'form_class': AdminRegisterForm
        }
    }
    
    info = role_info[role]
    form_class = info['form_class']
    
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            try:
                # Ambil password tanpa di-hash
                password = form.cleaned_data['password']
                username = form.cleaned_data['username']
                
                # Buat UserAccount dengan password plain text
                user = UserAccount.objects.create(
                    user_id=uuid.uuid4(),
                    username=username,
                    password=password
                )
                
                # Get atau create role
                role_obj, _ = Role.objects.get_or_create(
                    role_name=role,
                    defaults={'role_id': uuid.uuid4()}
                )
                
                # Buat AccountRole
                AccountRole.objects.create(
                    role_id=role_obj.role_id,
                    user_id=user.user_id
                )
                
                # Buat Customer, Organizer, atau Admin sesuai role
                if role == 'customer':
                    Customer.objects.create(
                        customer_id=uuid.uuid4(),
                        full_name=form.cleaned_data['full_name'],
                        phone_number=form.cleaned_data.get('phone_number', ''),
                        user_id=user.user_id
                    )
                
                elif role == 'organizer':
                    Organizer.objects.create(
                        organizer_id=uuid.uuid4(),
                        organizer_name=form.cleaned_data['organizer_name'],
                        contact_email=form.cleaned_data['contact_email'],
                        user_id=user.user_id
                    )
                
                elif role == 'admin':
                    # Admin hanya perlu UserAccount dan AccountRole
                    # Tidak perlu record tambahan di tabel admin
                    pass
                
                messages.success(request, f'Registrasi {info["title"]} berhasil! Silakan login.')
                return redirect('login')
                
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        else:
            # Form tidak valid, tampilkan error
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = form_class()
    
    context = {
        'form': form,
        'role': role,
        'role_title': info['title'],
        'role_icon': info['icon'],
        'role_description': info['description']
    }
    
    return render(request, 'register_form.html', context)


def verify_password(stored_password, input_password):
    """
    Verifikasi password plain text
    """
    return stored_password == input_password


def login_view(request):
    """View untuk halaman login"""
    login_error = None  # Variable untuk menyimpan error login
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            try:
                # Cari user berdasarkan username
                user = UserAccount.objects.get(username=username)
                
                # Verifikasi password (support hash dan plain text)
                if verify_password(user.password, password):
                    # Ambil role user
                    account_role = AccountRole.objects.filter(user_id=user.user_id).first()
                    role_obj = account_role.role if account_role else None
                    role_name = role_obj.role_name if role_obj else 'unknown'
                    
                    # Set session
                    request.session['user_id'] = str(user.user_id)
                    request.session['username'] = user.username
                    request.session['logged_in'] = True
                    request.session['role'] = role_name  # Set role di session
                    
                    # Tampilkan notifikasi hanya di dashboard, bukan di halaman login
                    messages.success(request, f'Login berhasil! Selamat datang, {username}')
                    return redirect('dashboard')
                else:
                    login_error = 'Username atau password salah!'
                
            except UserAccount.DoesNotExist:
                login_error = 'Username atau password salah!'
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form, 'login_error': login_error})

def logout_view(request):
    """View untuk logout"""
    request.session.flush()
    # Gunakan session storage messages agar tidak terlihat di halaman login
    return redirect('login')


def dashboard_view(request):
    """View untuk dashboard setelah login"""
    # Cek apakah user sudah login
    if not request.session.get('logged_in'):
        # Redirect tanpa warning message (untuk menghindari notifikasi bocor)
        return redirect('login')
    
    try:
        user_id = request.session.get('user_id')
        user = UserAccount.objects.get(user_id=user_id)
        
        # Ambil role user
        account_role = AccountRole.objects.filter(user_id=user_id).first()
        role_obj = account_role.role if account_role else None
        role_name = role_obj.role_name if role_obj else 'unknown'
        
        context = {
            'user': user,
            'role_name': role_name
        }
        
        return render(request, 'dashboard.html', context)
        
    except UserAccount.DoesNotExist:
        request.session.flush()
        # Redirect tanpa error message
        return redirect('login')
