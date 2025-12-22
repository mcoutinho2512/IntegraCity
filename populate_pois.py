"""
populate_pois.py - Popular POIs (Hospitais, Escolas, Abrigos, Câmeras)
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sitecor.settings')
django.setup()

from aplicativo.models import Hospital, Escola, Abrigo, Camera
from datetime import datetime

print('=' * 60)
print('🏥 POPULANDO POIs NO BANCO')
print('=' * 60)

# Limpar dados antigos
Hospital.objects.all().delete()
Escola.objects.all().delete()
Abrigo.objects.all().delete()
Camera.objects.all().delete()

# Hospitais
hospitais = [
    {'nome': 'Hospital Municipal Souza Aguiar', 'lat': -22.9131, 'lon': -43.1845, 'tipo': 'emergencia'},
    {'nome': 'Hospital Municipalizado Salgado Filho', 'lat': -22.8857, 'lon': -43.2802, 'tipo': 'geral'},
    {'nome': 'Hospital Municipal Lourenco Jorge', 'lat': -23.0080, 'lon': -43.4130, 'tipo': 'geral'},
    {'nome': 'Hospital Municipal Miguel Couto', 'lat': -22.9909, 'lon': -43.2311, 'tipo': 'geral'},
    {'nome': 'Hospital Municipal Rocha Maia', 'lat': -22.9173, 'lon': -43.2286, 'tipo': 'especializado'},
]

# Escolas
escolas = [
    {'nome': 'CIEP Brizolao 1', 'lat': -22.9200, 'lon': -43.2400, 'tipo': 'publica'},
    {'nome': 'Escola Municipal Tia Ciata', 'lat': -22.9100, 'lon': -43.2100, 'tipo': 'publica'},
    {'nome': 'Colegio Estadual Vicente Licinio', 'lat': -22.9500, 'lon': -43.1800, 'tipo': 'publica'},
    {'nome': 'CIEP Presidente Agostinho Neto', 'lat': -22.8900, 'lon': -43.2600, 'tipo': 'publica'},
]

# Abrigos
abrigos = [
    {'nome': 'Abrigo Comunitario Mangueira', 'lat': -22.9130, 'lon': -43.2400, 'capacidade': 200},
    {'nome': 'Abrigo Rocinha', 'lat': -22.9880, 'lon': -43.2480, 'capacidade': 300},
    {'nome': 'Abrigo Centro', 'lat': -22.9068, 'lon': -43.1729, 'capacidade': 150},
]

# Câmeras
cameras = [
    {'nome': 'Camera Tunel Reboucas', 'lat': -22.9475, 'lon': -43.1878, 'status': 'ativa'},
    {'nome': 'Camera Av Brasil km 10', 'lat': -22.8500, 'lon': -43.3000, 'status': 'ativa'},
    {'nome': 'Camera Linha Vermelha km 5', 'lat': -22.8700, 'lon': -43.2800, 'status': 'ativa'},
    {'nome': 'Camera Centro - Candelaria', 'lat': -22.9005, 'lon': -43.1737, 'status': 'ativa'},
]

# Popular Hospitais
for h in hospitais:
    try:
        Hospital.objects.create(
            nome=h['nome'],
            lat=h['lat'],
            lon=h['lon'],
            tipo=h.get('tipo', 'geral'),
            ativo=True
        )
        print(f'✅ Hospital: {h["nome"]}')
    except Exception as e:
        print(f'❌ Erro ao criar hospital: {e}')

# Popular Escolas
for e in escolas:
    try:
        Escola.objects.create(
            nome=e['nome'],
            lat=e['lat'],
            lon=e['lon'],
            tipo=e.get('tipo', 'publica'),
            ativo=True
        )
        print(f'✅ Escola: {e["nome"]}')
    except Exception as ex:
        print(f'❌ Erro ao criar escola: {ex}')

# Popular Abrigos
for a in abrigos:
    try:
        Abrigo.objects.create(
            nome=a['nome'],
            lat=a['lat'],
            lon=a['lon'],
            capacidade=a.get('capacidade', 100),
            ativo=True
        )
        print(f'✅ Abrigo: {a["nome"]}')
    except Exception as ex:
        print(f'❌ Erro ao criar abrigo: {ex}')

# Popular Câmeras
for c in cameras:
    try:
        Camera.objects.create(
            nome=c['nome'],
            lat=c['lat'],
            lon=c['lon'],
            status=c.get('status', 'ativa'),
            ativo=True
        )
        print(f'✅ Camera: {c["nome"]}')
    except Exception as ex:
        print(f'❌ Erro ao criar camera: {ex}')

print('\n' + '=' * 60)
print('✅ POIs criados com sucesso!')
print(f'🏥 {len(hospitais)} Hospitais')
print(f'🏫 {len(escolas)} Escolas')
print(f'🏠 {len(abrigos)} Abrigos')
print(f'📹 {len(cameras)} Câmeras')
print('=' * 60)