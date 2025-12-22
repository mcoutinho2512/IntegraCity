"""
populate_ocorrencias.py - Popular Ocorrências Espalhadas
"""

import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sitecor.settings')
django.setup()

from aplicativo.models import Ocorrencias

print('=' * 60)
print('🚨 ATUALIZANDO OCORRÊNCIAS')
print('=' * 60)

# Ocorrências espalhadas pelo Rio
ocorrencias_data = [
    {'incidente': 'Alagamento na Av. Brasil', 'lat': -22.8500, 'lng': -43.3000, 'tipo': 'Alagamento', 'prio': 'alta', 'bairro': 'Bonsucesso'},
    {'incidente': 'Queda de árvore na Barra', 'lat': -23.0045, 'lng': -43.3650, 'tipo': 'Queda de Árvore', 'prio': 'media', 'bairro': 'Barra da Tijuca'},
    {'incidente': 'Acidente na Linha Vermelha', 'lat': -22.8700, 'lng': -43.2800, 'tipo': 'Acidente', 'prio': 'alta', 'bairro': 'São Cristóvão'},
    {'incidente': 'Deslizamento em Santa Teresa', 'lat': -22.9200, 'lng': -43.1900, 'tipo': 'Deslizamento', 'prio': 'alta', 'bairro': 'Santa Teresa'},
    {'incidente': 'Buraco na via em Campo Grande', 'lat': -22.9089, 'lng': -43.5617, 'tipo': 'Via Danificada', 'prio': 'media', 'bairro': 'Campo Grande'},
    {'incidente': 'Semáforo com defeito em Copacabana', 'lat': -22.9711, 'lng': -43.1822, 'tipo': 'Sinalização', 'prio': 'baixa', 'bairro': 'Copacabana'},
    {'incidente': 'Princípio de incêndio em favela', 'lat': -22.9880, 'lng': -43.2480, 'tipo': 'Incêndio', 'prio': 'alta', 'bairro': 'Rocinha'},
    {'incidente': 'Vazamento de água na Tijuca', 'lat': -22.9249, 'lng': -43.2311, 'tipo': 'Vazamento', 'prio': 'media', 'bairro': 'Tijuca'},
]

# Atualizar as 8 ocorrências existentes
ocorrencias = list(Ocorrencias.objects.all()[:8])

for i, occ in enumerate(ocorrencias):
    if i < len(ocorrencias_data):
        data = ocorrencias_data[i]
        occ.incidente = data['incidente']
        occ.lat = data['lat']
        occ.lon = data['lng']
        occ.tipo_forma = data['tipo']
        occ.prio = data['prio']
        occ.bairro = data['bairro']
        occ.status = 'Em andamento'
        occ.data = datetime.now()
        occ.save()
        print(f'✅ {data["incidente"]} - {data["bairro"]}')

print('\n' + '=' * 60)
print('✅ 8 ocorrências atualizadas e espalhadas pelo Rio!')
print('=' * 60)