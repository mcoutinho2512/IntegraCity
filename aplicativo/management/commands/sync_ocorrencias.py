"""
sync_ocorrencias.py - Sincroniza ocorrências da API Hexagon
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from aplicativo.models import Ocorrencias
import requests

HEXAGON_API_BASE_URL = "https://api.corio-oncall.com.br/hxgnEvents/api"
HEXAGON_API_USERNAME = "APIOpenedEvent"
HEXAGON_API_PASSWORD = "12345"

EVENT_DICT = {
    "POP01": "ACIDENTE SEM VITIMA",
    "POP02": "ACIDENTE COM VITIMA",
    "POP03": "ACIDENTE COM OBITO",
    "POP04": "INCENDIO EM VEICULO",
    "POP05": "BOLSAO DE AGUA EM VIA",
    "POP20": "ATROPELAMENTO",
    "POP21": "AFUNDAMENTO DE PISTA OU BURACO NA VIA",
}

PRIORIDADE_DICT = {
    1: "BAIXA",
    2: "MÉDIA",
    3: "ALTA",
    4: "MUITO ALTA"
}

class Command(BaseCommand):
    help = 'Sincroniza ocorrências da API Hexagon'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando sincronização de ocorrências...')
        
        try:
            # Autenticar
            token = self.authenticate()
            self.stdout.write(f'✅ Autenticado com sucesso')
            
            # Buscar ocorrências
            ocorrencias = self.fetch_ocorrencias(token)
            self.stdout.write(f'📥 {len(ocorrencias)} ocorrências encontradas')
            
            # Salvar no banco
            salvas = self.salvar_ocorrencias(ocorrencias)
            self.stdout.write(self.style.SUCCESS(f'✅ {salvas} ocorrências salvas!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro: {e}'))
            import traceback
            traceback.print_exc()
    
    def authenticate(self):
        """Autenticar na API Hexagon"""
        url = f"{HEXAGON_API_BASE_URL}/Events/Login"
        payload = {
            "UserName": HEXAGON_API_USERNAME,
            "Password": HEXAGON_API_PASSWORD
        }
        
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        
        data = resp.json()
        token = data.get("AccessToken")
        
        if not token:
            raise RuntimeError(f"Falha na autenticação: {data}")
        
        return token
    
    def fetch_ocorrencias(self, token):
        """Buscar ocorrências abertas"""
        url = f"{HEXAGON_API_BASE_URL}/Events/OpenedEvents"
        payload = {"token": token}
        
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        
        return resp.json()
    
    def salvar_ocorrencias(self, ocorrencias):
        """Salvar ocorrências no banco"""
        contador = 0
        
        for item in ocorrencias:
            event_id = str(item.get("EventId"))
            
            # Verificar se já existe usando id_c
            if Ocorrencias.objects.filter(id_c=event_id).exists():
                continue
            
            # Criar nova ocorrência
            Ocorrencias.objects.create(
                id_c=event_id,
                incidente=EVENT_DICT.get(item.get("AgencyEventTypeCode"), "OUTROS"),
                location=item.get("Location", "Sem descrição"),
                lat=item.get("Latitude"),
                lon=item.get("Longitude"),
                prio=PRIORIDADE_DICT.get(item.get("Priority"), "BAIXA"),
                status='Em andamento',
                data=timezone.now()
            )
            
            contador += 1
        
        return contador