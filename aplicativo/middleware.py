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
    ])
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Executar DEPOIS que o usuário já foi autenticado
        process_view é executado DEPOIS do AuthenticationMiddleware
        """
        # Usar path_info para ignorar o FORCE_SCRIPT_NAME (/siscor)
        path = getattr(request, 'path_info', request.path)

        # Se é URL pública, permitir
        if any(path.startswith(url) for url in self.PUBLIC_URLS):
            return None

        # AGORA o request.user existe!
        if not request.user.is_authenticated:
            return redirect('login')

        return None
    
    def process_response(self, request, response):
        """Adicionar headers de segurança"""
        path = getattr(request, 'path_info', request.path)
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
