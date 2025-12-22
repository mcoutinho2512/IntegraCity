"""
populate_pluviometros.py - Popular Pluviômetros (CORRIGIDO)
"""

import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sitecor.settings')
django.setup()

from aplicativo.models import EstacaoPlv, DadosPlv

print('=' * 60)
print('🌧️ POPULANDO PLUVIÔMETROS')
print('=' * 60)

# Limpar dados antigos
print('�  Limpando dados antigos...')
DadosPlv.objects.all().delete()
EstacaoPlv.objects.all().delete()

# Estações de Pluviômetros no Rio
estacoes_data = [
    {'nome': 'Bangu', 'lat': -22.8792, 'lon': -43.4661, 'id_e': 'EST001'},
    {'nome': 'Santa Cruz', 'lat': -22.9199, 'lon': -43.6889, 'id_e': 'EST002'},
    {'nome': 'Campo Grande', 'lat': -22.9089, 'lon': -43.5617, 'id_e': 'EST003'},
    {'nome': 'Jardim Botanico', 'lat': -22.9664, 'lon': -43.2245, 'id_e': 'EST004'},
    {'nome': 'Alto da Boa Vista', 'lat': -22.9562, 'lon': -43.2847, 'id_e': 'EST005'},
    {'nome': 'Tijuca', 'lat': -22.9249, 'lon': -43.2311, 'id_e': 'EST006'},
    {'nome': 'Copacabana', 'lat': -22.9711, 'lon': -43.1822, 'id_e': 'EST007'},
    {'nome': 'Centro', 'lat': -22.9068, 'lon': -43.1729, 'id_e': 'EST008'},
    {'nome': 'Barra da Tijuca', 'lat': -23.0045, 'lon': -43.3650, 'id_e': 'EST009'},
    {'nome': 'Rocinha', 'lat': -22.9880, 'lon': -43.2480, 'id_e': 'EST010'},
]

import random

for est_data in estacoes_data:
    try:
        estacao = EstacaoPlv.objects.create(
            nome=est_data['nome'],
            lat=est_data['lat'],
            lon=est_data['lon'],
            id_e=est_data['id_e'],
            municipio='Rio de Janeiro',
            fonte='ALERTA RIO'
        )
        
        agora = datetime.now()
        DadosPlv.objects.create(
            estacao=estacao,
            data=agora,
            data_u=agora,
            data_t=agora.strftime('%Y-%m-%d %H:%M:%S'),
            chuva_i=round(random.uniform(0, 2), 1),
            chuva_1=round(random.uniform(0, 5), 1),
            chuva_4=round(random.uniform(0, 15), 1),
            chuva_24=round(random.uniform(0, 40), 1),
            chuva_96=round(random.uniform(0, 100), 1),
            chuva_30=round(random.uniform(0, 200), 1)
        )
        
        print(f' {est_data["nome"]} criada com sucesso!')
        
    except Exception as e:
        print(f' Erro ao criar {est_data["nome"]}: {e}')

print('\n' + '=' * 60)
total = EstacaoPlv.objects.count()
print(f' {total} pluviômetros criados no banco!')
print('=' * 60)
