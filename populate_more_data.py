import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sitecor.settings')
django.setup()

from aplicativo.models import Sirene, DadosSirene, Ocorrencias
from datetime import datetime, timedelta
import random

print('Adicionando mais dados')

print('Criando sirenes')
novas_sirenes = [
    {'nome': 'Sirene Santa Marta', 'lat': '-22.9492', 'lon': '-43.1853', 'id_e': 'SIR005'},
    {'nome': 'Sirene Providencia', 'lat': '-22.8986', 'lon': '-43.1889', 'id_e': 'SIR006'},
    {'nome': 'Sirene Alemao', 'lat': '-22.8667', 'lon': '-43.2639', 'id_e': 'SIR007'},
    {'nome': 'Sirene Mangueira', 'lat': '-22.9025', 'lon': '-43.2347', 'id_e': 'SIR008'},
    {'nome': 'Sirene Jacarezinho', 'lat': '-22.8828', 'lon': '-43.2594', 'id_e': 'SIR009'},
    {'nome': 'Sirene Mare', 'lat': '-22.8544', 'lon': '-43.2447', 'id_e': 'SIR010'},
]

for s in novas_sirenes:
    try:
        sirene = Sirene.objects.create(
            nome=s['nome'],
            lat=s['lat'],
            lon=s['lon'],
            id_e=s['id_e'],
            municipio='Rio de Janeiro',
            fonte='COR'
        )
        DadosSirene.objects.create(
            estacao=sirene,
            data=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            status='ativa',
            tipo=random.choice(['alta', 'media', 'baixa'])
        )
        print('OK: ' + s['nome'])
    except:
        print('Erro: ' + s['nome'])

print('Criando ocorrencias')
for i in range(5):
    try:
        Ocorrencias.objects.create(
            data=datetime.now() - timedelta(hours=i+3),
            gerencia='Zona Norte'
        )
        print('OK: ocorrencia ' + str(i))
    except:
        pass

print('TOTAL:')
print('Sirenes: ' + str(Sirene.objects.count()))
print('Ocorrencias: ' + str(Ocorrencias.objects.count()))