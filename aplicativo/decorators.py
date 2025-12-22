from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return redirect('dashboard')
    return wrapper

def operador_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.groups.filter(name='Operador').exists() or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        return redirect('dashboard')
    return wrapper