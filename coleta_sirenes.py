"""
coleta_sirenes.py - Coleta dados REAIS das Sirenes do Rio
"""

import os
import django
import requests
from datetime import datetime
from xml.etree import ElementTree

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sitecor.settings')
django.setup()

from aplicativo.models import Sirene, DadosSirene

def coletar_sirenes():
    """Busca sirenes da API oficial"""
    try:
        print('🚨 Buscando sirenes da API oficial...')
        
        timestamp = datetime.now().timestamp()
        url = f"http://websirene.rio.rj.gov.br/xml/sirenes.xml?nocache={timestamp}"
        
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            root = ElementTree.fromstring(response.content)
            
            sirenes_atualizadas = 0
            sirenes_criadas = 0
            
            for estacao in root.findall('estacao'):
                try:
                    id_sirene = estacao.get('id')
                    nome = estacao.get('nome', 'Sirene')
                    tipo_sirene = estacao.get('type', 'sir')
                    
                    localizacao = estacao.find('localizacao')
                    if localizacao is None:
                        continue
                    
                    lat = localizacao.get('latitude')
                    lon = localizacao.get('longitude')
                    bacia = localizacao.get('bacia', '')
                    
                    status_elem = estacao.find('status')
                    online = status_elem.get('online', 'False') if status_elem is not None else 'False'
                    status = status_elem.get('status', 'ds') if status_elem is not None else 'ds'
                    
                    if not lat or not lon:
                        continue
                    
                    status_texto = 'Online' if online == 'True' else 'Offline'
                    tipo_texto = 'Desligada' if status == 'ds' else 'Acionada'
                    
                    # Criar ou atualizar sirene
                    sirene, created = Sirene.objects.update_or_create(
                        id_e=id_sirene,
                        defaults={
                            'nome': nome,
                            'lat': float(lat),
                            'lon': float(lon),
                            'endereco': bacia if bacia != '-' else '',
                            'comunidade': nome.split()[0],
                            'municipio': 'Rio de Janeiro',
                            'fonte': 'Defesa Civil Rio'
                        }
                    )
                    
                    # Criar registro de status COM data_u ÚNICO
                    data_timestamp = datetime.now()
                    data_u_unico = f"{id_sirene}{data_timestamp.strftime('%Y%m%d%H%M%S%f')}"
                    
                    DadosSirene.objects.create(
                        estacao=sirene,
                        status=status_texto,
                        tipo=tipo_texto,
                        data=data_timestamp,
                        data_u=data_u_unico
                    )
                    
                    if created:
                        sirenes_criadas += 1
                    else:
                        sirenes_atualizadas += 1
                    
                    print(f'   ✅ {nome} ({status_texto} - {tipo_texto})')
                    
                except Exception as e:
                    print(f'   ⚠️  Erro ao processar {nome}: {e}')
                    continue
            
            print(f'\n✅ {sirenes_criadas} sirenes criadas')
            print(f'✅ {sirenes_atualizadas} sirenes atualizadas')
            print(f'📊 Total: {sirenes_criadas + sirenes_atualizadas} sirenes')
            return sirenes_criadas + sirenes_atualizadas
            
        else:
            print(f'❌ Erro na API: Status {response.status_code}')
            return 0
            
    except requests.exceptions.Timeout:
        print('❌ Timeout na API das sirenes')
        return 0
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return 0

if __name__ == '__main__':
    print('=' * 60)
    print('🚨 COLETANDO SIRENES DO RIO DE JANEIRO')
    print('=' * 60)
    
    total = coletar_sirenes()
    
    print('\n' + '=' * 60)
    print(f'✅ {total} sirenes processadas com sucesso!')
    print('=' * 60)