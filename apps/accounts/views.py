from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from audit.models import SecurityAuditLog, AuditEventType


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            
            # Audit Log Login
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
            SecurityAuditLog.objects.create(
                user=user,
                event_type=AuditEventType.LOGIN,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                path=request.path
            )
            return redirect('dashboard')
        else:
            messages.error(request, "Username atau password yang Anda masukkan tidak valid.")

    return render(request, 'accounts/login.html')


def logout_view(request):
    if request.user.is_authenticated:
        SecurityAuditLog.objects.create(
            user=request.user,
            event_type=AuditEventType.LOGOUT,
            ip_address=request.META.get('REMOTE_ADDR'),
            path=request.path
        )
        logout(request)
    return redirect('login')
