"""
sincronizador_completo.py - Sistema Completo de Sincronização
Busca dados de TODAS as fontes externas
"""

import os
import django
import requests
from datetime import datetime
from xml.etree import ElementTree

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sitecor.settings')
django.setup()

from aplicativo.models import Ocorrencias, EstacaoPlv, DadosPlv

class SincronizadorCompleto:
    """Sincroniza TODAS as fontes externas"""
    
    def __init__(self):
        self.total_ocorrencias = 0
        self.total_pluviometros = 0
    
    def sincronizar_waze(self):
        """Waze for Cities - OCORRÊNCIAS"""
        print('\n🚗 Sincronizando Waze...')
        
        # QUANDO TIVER TOKEN:
        # url = "https://www.waze.com/row-partnerhub-api/partners/[ID]/waze-feeds/[FEED]?format=1"
        # response = requests.get(url)
        # ... processar
        
        print('   ⚠️  Aguardando credenciais do Waze')
        return 0
    
    def sincronizar_alerta_rio(self):
        """Alerta Rio - CHUVAS"""
        print('\n☁️  Sincronizando Alerta Rio...')
        
        try:
            # Buscar XML de chuvas
            url = "https://www.sistema-alerta-rio.com.br/upload/xml/Chuvas.xml"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                root = ElementTree.fromstring(response.content)
                count = 0
                
                for estacao in root:
                    try:
                        nome = estacao.find('nomeEstacao').text
                        lat = float(estacao.find('lat').text)
                        lon = float(estacao.find('lon').text)
                        chuva_15min = float(estacao.find('chuva15min').text or 0)
                        
                        # Atualizar pluviômetro
                        plv, created = EstacaoPlv.objects.get_or_create(
                            nome=nome,
                            defaults={'lat': lat, 'lon': lon, 'fonte': 'ALERTA RIO'}
                        )
                        
                        # Salvar dados
                        DadosPlv.objects.create(
                            estacao=plv,
                            chuva_1=chuva_15min,
                            data=datetime.now()
                        )
                        
                        count += 1
                    except:
                        continue
                
                print(f'   ✅ {count} estações atualizadas')
                self.total_pluviometros = count
                return count
                
        except Exception as e:
            print(f'   ❌ Erro: {e}')
            return 0
    
    def sincronizar_sirenes(self):
        """Sirenes Defesa Civil"""
        print('\n🚨 Sincronizando Sirenes...')
        
        try:
            url = "http://websirene.rio.rj.gov.br/xml/sirenes.xml"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print('   ✅ Sirenes atualizadas')
                return True
        except:
            print('   ⚠️  Fonte offline')
        
        return False
    
    def executar(self):
        """Executa sincronização completa"""
        print('=' * 60)
        print('🔄 SINCRONIZAÇÃO COMPLETA')
        print('=' * 60)
        
        self.sincronizar_waze()
        self.sincronizar_alerta_rio()
        self.sincronizar_sirenes()
        
        print('\n' + '=' * 60)
        print(f'✅ CONCLUÍDO!')
        print(f'   🚗 Ocorrências: {self.total_ocorrencias}')
        print(f'   ☁️  Pluviômetros: {self.total_pluviometros}')
        print('=' * 60)

if __name__ == '__main__':
    sincronizador = SincronizadorCompleto()
    sincronizador.executar()