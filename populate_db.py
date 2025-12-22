# populate_db.py - Versão corrigida para estrutura real
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sitecor.settings')
django.setup()

from aplicativo.models import Sirene, DadosSirene, Evento, Ocorrencias, Local
from datetime import datetime, timedelta

print('Populando banco de dados...\n')

# Limpar
print('Limpando dados antigos...')
Sirene.objects.all().delete()
DadosSirene.objects.all().delete()
print('✓ Limpeza concluída\n')

# ============================================
# SIRENES (estrutura correta)
# ============================================
print('Criando Sirenes...')
sirenes_data = [
    {'nome': 'Sirene Rocinha', 'lat': '-22.9881', 'lon': '-43.2497', 'id_e': 'SIR001'},
    {'nome': 'Sirene Vidigal', 'lat': '-22.9925', 'lon': '-43.2318', 'id_e': 'SIR002'},
    {'nome': 'Sirene Alto da Boa Vista', 'lat': '-22.9647', 'lon': '-43.2844', 'id_e': 'SIR003'},
    {'nome': 'Sirene Morro dos Prazeres', 'lat': '-22.9158', 'lon': '-43.1842', 'id_e': 'SIR004'},
]

for s_data in sirenes_data:
    try:
        sirene = Sirene.objects.create(
            nome=s_data['nome'],
            lat=s_data['lat'],
            lon=s_data['lon'],
            id_e=s_data['id_e'],
            municipio='Rio de Janeiro',
            fonte='COR'
        )
        
        # Criar dados da sirene
        DadosSirene.objects.create(
            estacao=sirene,
            data=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            status='ativa',
            tipo='alta' if 'Rocinha' in s_data['nome'] else 'media'
        )
        print(f'  ✓ {s_data["nome"]}')
    except Exception as e:
        print(f'  ✗ {s_data["nome"]}: {str(e)[:50]}')

# ============================================
# LOCAIS (necessário para Eventos)
# ============================================
print('\nCriando Locais...')
locais_data = [
    {'nome': 'Centro', 'lat': '-22.9068', 'lon': '-43.1729'},
    {'nome': 'Cidade do Rock', 'lat': '-22.9771', 'lon': '-43.3951'},
    {'nome': 'Copacabana', 'lat': '-22.9711', 'lon': '-43.1822'},
]

locais_criados = []
for l_data in locais_data:
    try:
        local, created = Local.objects.get_or_create(
            nome=l_data['nome'],
            defaults={
                'lat': l_data['lat'],
                'lon': l_data['lon']
            }
        )
        locais_criados.append(local)
        if created:
            print(f'  ✓ {l_data["nome"]}')
    except Exception as e:
        print(f'  ✗ {l_data["nome"]}: {str(e)[:50]}')

# ============================================
# EVENTOS (estrutura correta)
# ============================================
if locais_criados:
    print('\nCriando Eventos...')
    eventos_data = [
        {'nome': 'Carnaval 2025', 'tipo': 'Carnaval: Desfiles', 'local_idx': 0},
        {'nome': 'Rock in Rio 2025', 'tipo': 'Musical', 'local_idx': 1},
        {'nome': 'Reveillon Copacabana', 'tipo': 'Réveillon', 'local_idx': 2},
    ]
    
    for e_data in eventos_data:
        try:
            if e_data['local_idx'] < len(locais_criados):
                evento = Evento.objects.create(
                    nome_evento=e_data['nome'],
                    endere=locais_criados[e_data['local_idx']],
                    tipo=e_data['tipo']
                )
                print(f'  ✓ {e_data["nome"]}')
        except Exception as e:
            print(f'  ✗ {e_data["nome"]}: {str(e)[:50]}')

# ============================================
# OCORRÊNCIAS (estrutura correta)
# ============================================
print('\nCriando Ocorrências...')
ocorrencias_data = [
    {'gerencia': 'Zona Norte', 'data_offset': 0},
    {'gerencia': 'Zona Sul', 'data_offset': 1},
    {'gerencia': 'Centro', 'data_offset': 2},
]

for i, o_data in enumerate(ocorrencias_data):
    try:
        # Data única para cada ocorrência
        data_ocorrencia = datetime.now() - timedelta(hours=o_data['data_offset'])
        
        Ocorrencias.objects.create(
            data=data_ocorrencia,
            gerencia=o_data['gerencia']
        )
        print(f'  ✓ Ocorrência {o_data["gerencia"]}')
    except Exception as e:
        print(f'  ✗ {o_data["gerencia"]}: {str(e)[:50]}')

print('\n✅ PROCESSO CONCLUÍDO!')
print(f'  - {Sirene.objects.count()} Sirenes')
print(f'  - {Evento.objects.count()} Eventos')
print(f'  - {Ocorrencias.objects.count()} Ocorrências')