"""
Views de Gerenciamento de Usuários - INTEGRACITY
Sistema completo de CRUD de usuários com permissões e auditoria
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from functools import wraps
import json

from .models import UserProfile, UserPermission, AuditLog, ROLE_DEFAULT_PERMISSIONS
from .forms import UserCreateForm, UserEditForm, PasswordResetByAdminForm


# ============================================
# DECORATORS DE PERMISSÃO
# ============================================

def admin_required(view_func):
    """Decorator para verificar se usuário é administrador"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Você precisa estar logado para acessar esta página.')
            return redirect('login')

        # Garantir que o usuário tem profile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        if not profile.can_manage_users():
            messages.error(request, 'Você não tem permissão para acessar esta página.')
            return redirect('cor_dashboard')

        return view_func(request, *args, **kwargs)
    return wrapper


def administrador_required(view_func):
    """Decorator para verificar se usuário é administrador"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Você precisa estar logado para acessar esta página.')
            return redirect('login')

        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        if not profile.is_admin():
            messages.error(request, 'Apenas Administradores podem acessar esta página.')
            return redirect('user_management')

        return view_func(request, *args, **kwargs)
    return wrapper


# Alias para compatibilidade
superadmin_required = administrador_required


# ============================================
# VIEWS DE GERENCIAMENTO DE USUÁRIOS
# ============================================

@login_required
@admin_required
def user_management(request):
    """Página principal de gerenciamento de usuários"""

    users = User.objects.select_related('profile').all().order_by('-date_joined')

    # Filtros
    search = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    if role_filter:
        users = users.filter(profile__role=role_filter)

    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'locked':
        users = users.filter(profile__locked_until__gt=timezone.now())

    # Paginação
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)

    # Estatísticas
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    locked_users = UserProfile.objects.filter(locked_until__gt=timezone.now()).count()

    context = {
        'users': users_page,
        'search': search,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'roles': UserProfile.ROLES,
        'total_users': total_users,
        'active_users': active_users,
        'locked_users': locked_users,
        'page_title': 'Gerenciamento de Usuários',
    }

    return render(request, 'users/user_management.html', context)


@login_required
@admin_required
def user_create(request):
    """Criar novo usuário"""

    if request.method == 'POST':
        form = UserCreateForm(request.POST, request_user=request.user)
        if form.is_valid():
            user = form.save()

            # Log de auditoria
            AuditLog.log(
                request=request,
                action='user_create',
                resource_type='User',
                resource_id=user.id,
                details={
                    'username': user.username,
                    'email': user.email,
                    'role': user.profile.role,
                    'full_name': user.get_full_name(),
                }
            )

            messages.success(request, f'Usuário "{user.username}" criado com sucesso!')
            return redirect('user_management')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = UserCreateForm(request_user=request.user)

    context = {
        'form': form,
        'action': 'Criar',
        'page_title': 'Criar Novo Usuário',
    }

    return render(request, 'users/user_form.html', context)


@login_required
@admin_required
def user_edit(request, user_id):
    """Editar usuário existente"""

    user_obj = get_object_or_404(User, id=user_id)

    # Garantir que o usuário tem profile
    profile, _ = UserProfile.objects.get_or_create(user=user_obj)

    # Administradores só podem ser editados por outros administradores
    if profile.role == 'administrador':
        request_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not request_profile.is_admin():
            messages.error(request, 'Você não tem permissão para editar Administradores.')
            return redirect('user_management')

    # Não pode editar a si mesmo via esta página (deve usar perfil)
    # Mas permitimos para administradores
    if user_obj == request.user and not request.user.profile.is_admin():
        messages.warning(request, 'Use a página de perfil para editar seus próprios dados.')
        return redirect('user_management')

    old_data = {
        'username': user_obj.username,
        'email': user_obj.email,
        'role': profile.role,
        'is_active': user_obj.is_active,
    }

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_obj, request_user=request.user)
        if form.is_valid():
            user = form.save()

            # Detectar mudanças para o log
            changes = {}
            if old_data['username'] != user.username:
                changes['username'] = {'old': old_data['username'], 'new': user.username}
            if old_data['email'] != user.email:
                changes['email'] = {'old': old_data['email'], 'new': user.email}
            if old_data['role'] != user.profile.role:
                changes['role'] = {'old': old_data['role'], 'new': user.profile.role}
            if old_data['is_active'] != user.is_active:
                changes['is_active'] = {'old': old_data['is_active'], 'new': user.is_active}

            # Log de auditoria
            AuditLog.log(
                request=request,
                action='user_edit',
                resource_type='User',
                resource_id=user.id,
                details={
                    'username': user.username,
                    'changes': changes,
                }
            )

            messages.success(request, f'Usuário "{user.username}" atualizado com sucesso!')
            return redirect('user_management')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = UserEditForm(instance=user_obj, request_user=request.user)

    context = {
        'form': form,
        'user_obj': user_obj,
        'action': 'Editar',
        'page_title': f'Editar Usuário: {user_obj.username}',
    }

    return render(request, 'users/user_form.html', context)


@login_required
@admin_required
def user_detail(request, user_id):
    """Detalhes do usuário"""

    user_obj = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user_obj)

    # Últimos logs do usuário
    recent_logs = AuditLog.objects.filter(user=user_obj).order_by('-timestamp')[:20]

    # Permissões customizadas
    custom_permissions = UserPermission.objects.filter(user=user_obj)

    # Permissões padrão do role
    role_permissions = ROLE_DEFAULT_PERMISSIONS.get(profile.role, {})

    context = {
        'user_obj': user_obj,
        'profile': profile,
        'recent_logs': recent_logs,
        'custom_permissions': custom_permissions,
        'role_permissions': role_permissions,
        'page_title': f'Detalhes: {user_obj.get_full_name() or user_obj.username}',
    }

    return render(request, 'users/user_detail.html', context)


@login_required
@admin_required
@require_http_methods(["POST"])
def user_toggle_status(request, user_id):
    """Ativar/Desativar usuário (AJAX)"""

    user_obj = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user_obj)

    # Não pode desativar a si mesmo
    if user_obj == request.user:
        return JsonResponse({
            'success': False,
            'error': 'Não é possível desativar seu próprio usuário.'
        })

    # Administradores só podem ser desativados por outros administradores
    if profile.role == 'administrador':
        request_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not request_profile.is_admin():
            return JsonResponse({
                'success': False,
                'error': 'Apenas Administradores podem desativar outros Administradores.'
            })

    # Toggle status
    user_obj.is_active = not user_obj.is_active
    user_obj.save(update_fields=['is_active'])

    action = 'user_activate' if user_obj.is_active else 'user_deactivate'

    # Log de auditoria
    AuditLog.log(
        request=request,
        action=action,
        resource_type='User',
        resource_id=user_obj.id,
        details={
            'username': user_obj.username,
            'new_status': 'active' if user_obj.is_active else 'inactive',
        }
    )

    return JsonResponse({
        'success': True,
        'is_active': user_obj.is_active,
        'message': f'Usuário {"ativado" if user_obj.is_active else "desativado"} com sucesso.'
    })


@login_required
@admin_required
@require_http_methods(["POST"])
def user_unlock(request, user_id):
    """Desbloquear usuário (AJAX)"""

    user_obj = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user_obj)

    if not profile.is_locked():
        return JsonResponse({
            'success': False,
            'error': 'Este usuário não está bloqueado.'
        })

    profile.unlock_account()

    # Log de auditoria
    AuditLog.log(
        request=request,
        action='user_unlock',
        resource_type='User',
        resource_id=user_obj.id,
        details={
            'username': user_obj.username,
        }
    )

    return JsonResponse({
        'success': True,
        'message': f'Usuário "{user_obj.username}" desbloqueado com sucesso.'
    })


@login_required
@admin_required
@require_http_methods(["POST"])
def user_delete(request, user_id):
    """Excluir usuário permanentemente (AJAX)"""

    user_obj = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user_obj)

    # Não pode excluir a si mesmo
    if user_obj == request.user:
        return JsonResponse({
            'success': False,
            'error': 'Não é possível excluir seu próprio usuário.'
        })

    # Administradores só podem ser excluídos por outros administradores
    if profile.role == 'administrador':
        request_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not request_profile.is_admin():
            return JsonResponse({
                'success': False,
                'error': 'Apenas Administradores podem excluir outros Administradores.'
            })

    username = user_obj.username

    # Log de auditoria (antes de excluir)
    AuditLog.log(
        request=request,
        action='user_delete',
        resource_type='User',
        resource_id=user_obj.id,
        details={
            'username': username,
            'email': user_obj.email,
            'role': profile.role,
        }
    )

    user_obj.delete()

    return JsonResponse({
        'success': True,
        'message': f'Usuário "{username}" excluído permanentemente.'
    })


@login_required
@admin_required
def user_reset_password(request, user_id):
    """Resetar senha de usuário"""

    user_obj = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user_obj)

    # Não pode resetar senha de administrador se não for administrador
    if profile.role == 'administrador':
        request_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not request_profile.is_admin():
            messages.error(request, 'Você não tem permissão para resetar senha de Administradores.')
            return redirect('user_management')

    if request.method == 'POST':
        form = PasswordResetByAdminForm(request.POST)
        if form.is_valid():
            user_obj.set_password(form.cleaned_data['new_password1'])
            user_obj.save()

            # Atualizar profile
            profile.must_change_password = form.cleaned_data.get('must_change_password', True)
            profile.save(update_fields=['must_change_password'])

            # Log de auditoria
            AuditLog.log(
                request=request,
                action='password_reset',
                resource_type='User',
                resource_id=user_obj.id,
                details={
                    'username': user_obj.username,
                    'must_change_password': profile.must_change_password,
                }
            )

            messages.success(request, f'Senha do usuário "{user_obj.username}" resetada com sucesso!')
            return redirect('user_management')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = PasswordResetByAdminForm()

    context = {
        'form': form,
        'user_obj': user_obj,
        'page_title': f'Resetar Senha: {user_obj.username}',
    }

    return render(request, 'users/user_reset_password.html', context)


# ============================================
# VIEWS DE PERMISSÕES
# ============================================

@login_required
@admin_required
def user_permissions(request, user_id):
    """Gerenciar permissões customizadas do usuário"""

    user_obj = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user_obj)

    # Administradores só podem ter permissões editadas por outros administradores
    if profile.role == 'administrador':
        request_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not request_profile.is_admin():
            messages.error(request, 'Você não tem permissão para editar permissões de Administradores.')
            return redirect('user_management')

    if request.method == 'POST':
        # Processar permissões
        try:
            permissions_data = json.loads(request.POST.get('permissions', '{}'))

            # Remover permissões antigas
            old_permissions = list(UserPermission.objects.filter(user=user_obj).values('resource', 'action'))
            UserPermission.objects.filter(user=user_obj).delete()

            # Criar novas permissões
            new_permissions = []
            for resource, actions in permissions_data.items():
                for action in actions:
                    UserPermission.objects.create(
                        user=user_obj,
                        resource=resource,
                        action=action,
                        created_by=request.user
                    )
                    new_permissions.append({'resource': resource, 'action': action})

            # Log de auditoria
            AuditLog.log(
                request=request,
                action='permission_grant',
                resource_type='UserPermission',
                resource_id=user_obj.id,
                details={
                    'username': user_obj.username,
                    'old_permissions': old_permissions,
                    'new_permissions': new_permissions,
                }
            )

            messages.success(request, f'Permissões de "{user_obj.username}" atualizadas com sucesso!')
            return redirect('user_management')

        except json.JSONDecodeError:
            messages.error(request, 'Erro ao processar permissões.')

    # Carregar permissões atuais
    current_permissions = {}
    for perm in UserPermission.objects.filter(user=user_obj):
        if perm.resource not in current_permissions:
            current_permissions[perm.resource] = []
        current_permissions[perm.resource].append(perm.action)

    # Permissões padrão do role
    role_permissions = ROLE_DEFAULT_PERMISSIONS.get(profile.role, {})

    context = {
        'user_obj': user_obj,
        'profile': profile,
        'current_permissions': current_permissions,
        'current_permissions_json': json.dumps(current_permissions),
        'role_permissions': role_permissions,
        'all_resources': UserPermission.RESOURCES,
        'all_actions': UserPermission.ACTIONS,
        'page_title': f'Permissões: {user_obj.username}',
    }

    return render(request, 'users/user_permissions.html', context)


@login_required
@admin_required
def user_module_permissions(request, user_id):
    """Gerenciar permissões de acesso a módulos do usuário"""

    user_obj = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user_obj)

    # Administradores não podem ter módulos alterados (sempre têm acesso total)
    if profile.role == 'administrador':
        messages.warning(request, 'Administradores sempre têm acesso a todos os módulos.')
        return redirect('user_management')

    # Não pode editar a si mesmo
    if user_obj == request.user:
        messages.warning(request, 'Você não pode editar suas próprias permissões de módulo.')
        return redirect('user_management')

    if request.method == 'POST':
        try:
            # Obter módulos selecionados do formulário
            selected_modules = request.POST.getlist('modules')

            # Validar que são módulos válidos
            valid_modules = [m[0] for m in UserProfile.MODULES]
            selected_modules = [m for m in selected_modules if m in valid_modules]

            # Salvar módulos
            old_modules = profile.allowed_modules or []
            profile.allowed_modules = selected_modules
            profile.save(update_fields=['allowed_modules'])

            # Log de auditoria
            AuditLog.log(
                request=request,
                action='permission_grant',
                resource_type='ModulePermission',
                resource_id=user_obj.id,
                details={
                    'username': user_obj.username,
                    'old_modules': old_modules,
                    'new_modules': selected_modules,
                }
            )

            messages.success(request, f'Permissões de módulos de "{user_obj.username}" atualizadas com sucesso!')
            return redirect('user_management')

        except Exception as e:
            messages.error(request, f'Erro ao salvar permissões: {str(e)}')

    # Módulos atuais (ou padrão do perfil)
    current_modules = profile.get_allowed_modules()
    default_modules = profile.DEFAULT_MODULES.get(profile.role, [])

    context = {
        'user_obj': user_obj,
        'profile': profile,
        'all_modules': UserProfile.MODULES,
        'current_modules': current_modules,
        'default_modules': default_modules,
        'page_title': f'Permissões de Módulos: {user_obj.get_full_name() or user_obj.username}',
    }

    return render(request, 'users/user_module_permissions.html', context)


@login_required
@admin_required
@require_http_methods(["POST"])
def api_user_module_permissions(request, user_id):
    """API: Atualizar permissões de módulos (AJAX)"""

    user_obj = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user_obj)

    # Administradores não podem ter módulos alterados
    if profile.role == 'administrador':
        return JsonResponse({
            'success': False,
            'error': 'Administradores sempre têm acesso a todos os módulos.'
        })

    try:
        data = json.loads(request.body)
        modules = data.get('modules', [])

        # Validar módulos
        valid_modules = [m[0] for m in UserProfile.MODULES]
        modules = [m for m in modules if m in valid_modules]

        # Salvar
        old_modules = profile.allowed_modules or []
        profile.allowed_modules = modules
        profile.save(update_fields=['allowed_modules'])

        # Log de auditoria
        AuditLog.log(
            request=request,
            action='permission_grant',
            resource_type='ModulePermission',
            resource_id=user_obj.id,
            details={
                'username': user_obj.username,
                'old_modules': old_modules,
                'new_modules': modules,
            }
        )

        return JsonResponse({
            'success': True,
            'message': f'Permissões de "{user_obj.username}" atualizadas com sucesso.',
            'modules': modules,
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados inválidos.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ============================================
# VIEWS DE AUDITORIA
# ============================================

@login_required
@admin_required
def audit_logs(request):
    """Visualizar logs de auditoria"""

    logs = AuditLog.objects.select_related('user').all()

    # Filtros
    user_filter = request.GET.get('user', '').strip()
    action_filter = request.GET.get('action', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    success_filter = request.GET.get('success', '')

    if user_filter:
        logs = logs.filter(
            Q(user__username__icontains=user_filter) |
            Q(user__first_name__icontains=user_filter) |
            Q(user__last_name__icontains=user_filter)
        )

    if action_filter:
        logs = logs.filter(action=action_filter)

    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)

    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)

    if success_filter == 'true':
        logs = logs.filter(success=True)
    elif success_filter == 'false':
        logs = logs.filter(success=False)

    # Paginação
    paginator = Paginator(logs, 50)
    page = request.GET.get('page', 1)
    logs_page = paginator.get_page(page)

    context = {
        'logs': logs_page,
        'user_filter': user_filter,
        'action_filter': action_filter,
        'date_from': date_from,
        'date_to': date_to,
        'success_filter': success_filter,
        'actions': AuditLog.ACTIONS,
        'page_title': 'Logs de Auditoria',
    }

    return render(request, 'users/audit_logs.html', context)


@login_required
@admin_required
def audit_log_detail(request, log_id):
    """Detalhes de um log de auditoria (AJAX)"""

    log = get_object_or_404(AuditLog, id=log_id)

    data = {
        'id': str(log.id),
        'user': log.user.username if log.user else 'Anônimo',
        'user_full_name': log.user.get_full_name() if log.user else 'N/A',
        'action': log.get_action_display(),
        'action_code': log.action,
        'resource_type': log.resource_type,
        'resource_id': log.resource_id,
        'details': log.details,
        'ip_address': log.ip_address,
        'user_agent': log.user_agent,
        'timestamp': log.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
        'success': log.success,
        'error_message': log.error_message,
    }

    return JsonResponse(data)


# ============================================
# API ENDPOINTS
# ============================================

@login_required
@admin_required
def api_users_list(request):
    """API: Lista de usuários para autocomplete/select"""

    search = request.GET.get('q', '').strip()

    users = User.objects.filter(is_active=True)

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    users = users[:20]

    data = [
        {
            'id': u.id,
            'username': u.username,
            'full_name': u.get_full_name() or u.username,
            'email': u.email,
        }
        for u in users
    ]

    return JsonResponse({'results': data})


@login_required
@admin_required
def api_users_stats(request):
    """API: Estatísticas de usuários"""

    from django.db.models import Count

    total = User.objects.count()
    active = User.objects.filter(is_active=True).count()
    inactive = User.objects.filter(is_active=False).count()
    locked = UserProfile.objects.filter(locked_until__gt=timezone.now()).count()

    by_role = UserProfile.objects.values('role').annotate(count=Count('role'))
    role_stats = {item['role']: item['count'] for item in by_role}

    # Logins recentes (últimas 24h)
    from datetime import timedelta
    yesterday = timezone.now() - timedelta(days=1)
    recent_logins = AuditLog.objects.filter(
        action='login',
        success=True,
        timestamp__gte=yesterday
    ).count()

    return JsonResponse({
        'total': total,
        'active': active,
        'inactive': inactive,
        'locked': locked,
        'by_role': role_stats,
        'recent_logins_24h': recent_logins,
    })
