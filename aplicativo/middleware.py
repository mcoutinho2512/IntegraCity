from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import time

class SecurityMiddleware(MiddlewareMixin):
    """Middleware de segurança - APÓS AuthenticationMiddleware"""

    # URLs publicas (que nao precisam de login)
    # SEGURANCA: APIs restritas - apenas endpoints especificos sao publicos
    PUBLIC_URLS = getattr(settings, 'PUBLIC_URLS', [
        '/login/',
        '/logout/',
        '/admin/',
        '/static/',
        '/media/',
        # APIs publicas especificas (apenas leitura, sem dados sensiveis)
        '/api/estagio/',
        '/api/estagio-atual/',
        '/api/estagio-externo/',
        # APIs de sirenes, chuvas e pluviômetros (Defesa Civil RJ - dados públicos)
        '/api/chuvas-defesa-civil/',
        '/api/sirenes-defesa-civil/',
        '/api/sirenes-chuvas/',
        '/api/pluviometros-defesa-civil/',
        # Camera embed proxy (usado dentro de iframe no modal)
        '/camera/embed/',
        '/api/camera/',
    ])

    # APIs que gerenciam sua própria autenticação (retornam JSON 401 em vez de redirect)
    # Isso é necessário para que o JavaScript possa detectar sessão expirada corretamente
    API_SELF_AUTH_URLS = [
        '/api/alertas-confirmados/',
    ]

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Executar DEPOIS que o usuário já foi autenticado
        process_view é executado DEPOIS do AuthenticationMiddleware
        """
        # Usar path_info para ignorar o FORCE_SCRIPT_NAME (/integracity)
        path = getattr(request, 'path_info', request.path)

        # Se é URL pública, permitir
        if any(path.startswith(url) for url in self.PUBLIC_URLS):
            return None

        # APIs que gerenciam própria autenticação - deixar a view retornar JSON 401
        if any(path.startswith(url) for url in self.API_SELF_AUTH_URLS):
            return None

        # AGORA o request.user existe!
        if not request.user.is_authenticated:
            return redirect('login')

        return None
    
    def process_response(self, request, response):
        """Adicionar headers de segurança"""
        path = getattr(request, 'path_info', request.path)

        # Permitir iframe para endpoints de embed
        if path.startswith('/camera/embed/'):
            response['X-Frame-Options'] = 'SAMEORIGIN'
            return response

        if path.startswith('/api/camera/') and path.endswith('/stream/') and request.GET.get('embed') == '1':
            response['X-Frame-Options'] = 'SAMEORIGIN'
            return response

        # Prevenir clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Prevenir MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # XSS Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Middleware para limitar tentativas de login"""
    
    attempts = {}  # Dicionário para rastrear tentativas
    
    def process_request(self, request):
        """Limitar tentativas de login por IP"""
        path = getattr(request, 'path_info', request.path)
        if path == '/login/' and request.method == 'POST':
            ip = self.get_client_ip(request)
            current_time = time.time()
            
            # Limpar tentativas antigas (mais de 15 minutos)
            self.attempts = {k: v for k, v in self.attempts.items() 
                           if current_time - v['time'] < 900}
            
            # Verificar se IP já tem tentativas
            if ip in self.attempts:
                attempts_count = self.attempts[ip]['count']
                last_attempt = self.attempts[ip]['time']
                
                # Se mais de 5 tentativas em 15 minutos, bloquear
                if attempts_count >= 5 and current_time - last_attempt < 900:
                    from django.http import HttpResponseForbidden
                    return HttpResponseForbidden(
                        '<h1 style="text-align:center;margin-top:100px;color:#ef4444;">🚫 Muitas tentativas de login.<br>Tente novamente em 15 minutos.</h1>'
                    )
                
                # Incrementar contador
                self.attempts[ip]['count'] += 1
                self.attempts[ip]['time'] = current_time
            else:
                # Primeira tentativa
                self.attempts[ip] = {'count': 1, 'time': current_time}
        
        return None
    
    def get_client_ip(self, request):
        """Obter IP real do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LoginSecurityMiddleware(MiddlewareMixin):
    """Middleware para segurança de login baseada em UserProfile"""

    def process_request(self, request):
        """Verificar se usuário está bloqueado ou precisa trocar senha"""
        if not request.user.is_authenticated:
            return None

        path = getattr(request, 'path_info', request.path)

        # Ignorar URLs estáticas e de logout
        ignore_paths = ['/static/', '/media/', '/logout/', '/admin/']
        if any(path.startswith(p) for p in ignore_paths):
            return None

        try:
            from aplicativo.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=request.user)

            # Verificar se conta está bloqueada
            if profile.is_locked():
                from django.contrib.auth import logout
                from django.contrib import messages
                logout(request)
                messages.error(request, 'Sua conta está temporariamente bloqueada. Tente novamente mais tarde.')
                return redirect('login')

            # Atualizar último IP de login
            ip = self.get_client_ip(request)
            if profile.last_login_ip != ip:
                profile.last_login_ip = ip
                profile.save(update_fields=['last_login_ip'])

        except Exception:
            pass

        return None

    def get_client_ip(self, request):
        """Obter IP real do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip


class ModuleAccessMiddleware(MiddlewareMixin):
    """Middleware para verificar acesso a módulos por usuário"""

    # Mapeamento de URLs para módulos
    URL_MODULE_MAP = {
        # Dashboard
        '/cor/': 'dashboard',
        '/cor': 'dashboard',
        '/api/alertas': 'dashboard',
        '/api/estatisticas': 'dashboard',
        '/api/waze': 'dashboard',
        '/api/brt': 'dashboard',
        '/api/estagio': 'dashboard',
        '/meteorologia/': 'dashboard',
        '/mobilidade/': 'dashboard',

        # Ocorrências
        '/ocorrencias/': 'ocorrencias',
        '/ocorrencia/': 'ocorrencias',
        '/api/ocorrencias': 'ocorrencias',
        '/api/pops': 'ocorrencias',

        # Eventos
        '/eventos/': 'eventos',
        '/evento/': 'eventos',
        '/api/eventos': 'eventos',

        # Áreas
        '/areas/': 'areas',
        '/area/': 'areas',
        '/api/areas': 'areas',

        # Matriz
        '/matriz/': 'matriz',
        '/api/matriz': 'matriz',

        # Câmeras
        '/cameras/': 'cameras',
        '/camera/': 'cameras',
        '/video/': 'cameras',
        '/api/camera': 'cameras',

        # Usuários
        '/usuarios/': 'usuarios',
        '/usuario/': 'usuarios',
    }

    # URLs que não precisam de verificação de módulo
    EXEMPT_URLS = [
        '/login/',
        '/logout/',
        '/admin/',
        '/static/',
        '/media/',
        '/api/sirenes',
        '/api/chuvas',
        '/api/pluviometros',
    ]

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Verificar se usuário tem acesso ao módulo"""
        if not request.user.is_authenticated:
            return None

        path = getattr(request, 'path_info', request.path)

        # Ignorar URLs isentas
        if any(path.startswith(url) for url in self.EXEMPT_URLS):
            return None

        # Identificar o módulo
        module = None
        for url_prefix, mod in self.URL_MODULE_MAP.items():
            if path.startswith(url_prefix):
                module = mod
                break

        # Se não encontrou módulo correspondente, permitir (URLs não mapeadas)
        if not module:
            return None

        # Verificar acesso ao módulo
        try:
            from aplicativo.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={'role': 'operador'}
            )

            if not profile.has_module_access(module):
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden(
                    '''<!DOCTYPE html>
                    <html>
                    <head>
                        <title>Acesso Negado</title>
                        <style>
                            body {
                                font-family: 'Segoe UI', sans-serif;
                                background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
                                height: 100vh;
                                margin: 0;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                color: white;
                            }
                            .container {
                                text-align: center;
                                padding: 40px;
                                background: rgba(255,255,255,0.1);
                                border-radius: 16px;
                                backdrop-filter: blur(10px);
                            }
                            h1 { font-size: 4rem; margin: 0; color: #ef4444; }
                            p { font-size: 1.2rem; color: #94a3b8; }
                            a {
                                display: inline-block;
                                margin-top: 20px;
                                padding: 12px 24px;
                                background: #3b82f6;
                                color: white;
                                text-decoration: none;
                                border-radius: 8px;
                            }
                            a:hover { background: #2563eb; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>🚫 403</h1>
                            <p>Você não tem permissão para acessar este módulo.</p>
                            <p>Contate o administrador do sistema para solicitar acesso.</p>
                            <a href="/integracity/cor/">← Voltar ao Dashboard</a>
                        </div>
                    </body>
                    </html>'''
                )

        except Exception:
            pass

        return None
