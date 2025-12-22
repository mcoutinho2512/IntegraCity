"""
populate_infraestrutura.py - Popular Escolas e Bens Tombados
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sitecor.settings')
django.setup()

from aplicativo.models import EscolasMunicipais, BensProtegidos

print('=' * 60)
print('🏫 POPULANDO INFRAESTRUTURA')
print('=' * 60)

# Limpar
EscolasMunicipais.objects.all().delete()
BensProtegidos.objects.all().delete()

# Escolas Municipais
escolas = [
    {'nome': 'CIEP Brizolao 1', 'x': -43.2400, 'y': -22.9200, 'endereco': 'Av. Brasil, 1000', 'bairro': 'Centro', 'telefone': '(21) 3333-4444'},
    {'nome': 'Escola Municipal Tia Ciata', 'x': -43.2100, 'y': -22.9100, 'endereco': 'Rua da Prainha, 100', 'bairro': 'Saúde', 'telefone': '(21) 2222-3333'},
    {'nome': 'Colégio Estadual Vicente Licinio', 'x': -43.1800, 'y': -22.9500, 'endereco': 'Rua Senador Pompeu, 50', 'bairro': 'Centro', 'telefone': '(21) 3344-5566'},
    {'nome': 'CIEP Presidente Agostinho Neto', 'x': -43.2600, 'y': -22.8900, 'endereco': 'Rua São Cristóvão, 200', 'bairro': 'São Cristóvão', 'telefone': '(21) 2555-6677'},
    {'nome': 'Escola Municipal Paulo Freire', 'x': -43.3100, 'y': -22.9300, 'endereco': 'Av. Maracanã, 500', 'bairro': 'Tijuca', 'telefone': '(21) 2888-9999'},
]

print('\n🏫 Criando Escolas...')
for escola in escolas:
    EscolasMunicipais.objects.create(
        nome=escola['nome'],
        x=escola['x'],
        y=escola['y'],
        endereco=escola['endereco'],
        bairro=escola['bairro'],
        telefone=escola.get('telefone', '')
    )
    print(f'✅ {escola["nome"]}')

# Bens Tombados
bens = [
    {'np': 'Teatro Municipal', 'x': -43.1759, 'y': -22.9082, 'rua': 'Av. Rio Branco', 'grau_de_pr': 'Alto'},
    {'np': 'Museu Nacional de Belas Artes', 'x': -43.1757, 'y': -22.9102, 'rua': 'Av. Rio Branco', 'grau_de_pr': 'Alto'},
    {'np': 'Biblioteca Nacional', 'x': -43.1754, 'y': -22.9099, 'rua': 'Av. Rio Branco', 'grau_de_pr': 'Alto'},
    {'np': 'Palácio Tiradentes', 'x': -43.1732, 'y': -22.9067, 'rua': 'Rua Primeiro de Março', 'grau_de_pr': 'Alto'},
    {'np': 'Igreja da Candelária', 'x': -43.1737, 'y': -22.9005, 'rua': 'Praça Pio X', 'grau_de_pr': 'Alto'},
    {'np': 'Arcos da Lapa', 'x': -43.1791, 'y': -22.9133, 'rua': 'Lapa', 'grau_de_pr': 'Alto'},
]

print('\n🏛️ Criando Bens Tombados...')
for bem in bens:
    BensProtegidos.objects.create(
        np=bem['np'],
        x=bem['x'],
        y=bem['y'],
        rua=bem['rua'],
        grau_de_pr=bem.get('grau_de_pr', 'Médio')
    )
    print(f'✅ {bem["np"]}')

print('\n' + '=' * 60)
print(f'✅ {len(escolas)} Escolas criadas!')
print(f'✅ {len(bens)} Bens Tombados criados!')
print('=' * 60)