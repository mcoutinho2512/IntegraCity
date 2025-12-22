"""
sincronizador_waze.py - Sincroniza Ocorrências do Waze
"""

import os
import django
import requests
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sitecor.settings')
django.setup()

from aplicativo.models import Ocorrencias

# URL DO WAZE (substituir pelo token correto)
WAZE_URL = "https://www.waze.com/row-partnerhub-api/partners/SEU_PARTNER_ID/waze-feeds/SEU_FEED_ID?format=1"

def sincronizar_waze():
    """Busca alertas do Waze e cria ocorrências"""
    try:
        print('🚗 Buscando dados do Waze...')
        
        # QUANDO TIVER O TOKEN REAL, DESCOMENTE:
        # response = requests.get(WAZE_URL)
        # data = response.json()
        
        # POR ENQUANTO: SIMULAÇÃO
        print('⚠️  Token do Waze não configurado')
        print('📝 Pergunte ao chefe sobre acesso ao Waze for Cities')
        
        return 0
        
        # CÓDIGO REAL (quando tiver token):
        # for alert in data.get('alerts', []):
        #     tipo_mapeado = mapear_tipo_waze(alert.get('type'))
        #     
        #     Ocorrencias.objects.update_or_create(
        #         id_c=alert.get('uuid'),  # ID único do Waze
        #         defaults={
        #             'incidente': alert.get('street', 'Ocorrência Waze'),
        #             'lat': alert.get('location', {}).get('y'),
        #             'lon': alert.get('location', {}).get('x'),
        #             'tipo_forma': tipo_mapeado,
        #             'prio': mapear_prioridade(alert.get('subtype')),
        #             'status': 'Em andamento',
        #             'data': datetime.now()
        #         }
        #     )
        
    except Exception as e:
        print(f'❌ Erro: {e}')
        return 0

def mapear_tipo_waze(tipo_waze):
    """Mapeia tipos do Waze para tipos internos"""
    mapa = {
        'ACCIDENT': 'Acidente',
        'JAM': 'Congestionamento',
        'WEATHERHAZARD': 'Condição Climática',
        'ROAD_CLOSED': 'Via Interditada',
        'HAZARD': 'Perigo na Via'
    }
    return mapa.get(tipo_waze, 'Outros')

def mapear_prioridade(subtipo):
    """Mapeia subtipo para prioridade"""
    if subtipo in ['ACCIDENT_MAJOR', 'HAZARD_ON_ROAD']:
        return 'alta'
    elif subtipo in ['ACCIDENT_MINOR', 'JAM_HEAVY_TRAFFIC']:
        return 'media'
    return 'baixa'

if __name__ == '__main__':
    print('=' * 60)
    print('🚗 SINCRONIZADOR WAZE')
    print('=' * 60)
    total = sincronizar_waze()
    print(f'\n✅ {total} ocorrências sincronizadas')
    print('=' * 60)
```

---

## 📋 **PERGUNTE AO SEU CHEFE:**
```
"Chefe, encontrei que o sistema antigo usa Waze for Cities.
Preciso do token/credencial de acesso para integrar no novo sistema.

URL que o sistema antigo usa:
https://www.waze.com/row-partnerhub-api/partners/[ID]/waze-feeds/[FEED_ID]

Pode me passar o Partner ID e Feed ID?"