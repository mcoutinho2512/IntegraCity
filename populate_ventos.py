"""
populate_ventos.py - Popular Estações de Vento (CORRIGIDO)
"""

import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sitecor.settings')
django.setup()

from aplicativo.models import EstacaoMet, DadosMet

print('=' * 60)
print('🌬️ POPULANDO ESTAÇÕES DE VENTO')
print('=' * 60)

dados_api = """Santa Cruz ;-22.93239974975586;-43.71910095214844;31.0;29.0;de NW para SE;5.4;2025.09.04 1700;
Vila Militar;-22.86138888;-43.41138888;29.5;62.0;de N para S;5.1;20/10/2022 1700;
Marambaia;-23.05027777;-43.59555555;24.5;15.0;de SE para NW;4.8;22/12/2022 1700;
Campo Délio Jardim de Mattos ;-22.875099;-43.384701;31.0;29.0;de N para S;3.6;2025.09.04 1700;
Santos Dumont ;-22.910499572799996;-43.1631011963;26.0;54.0;de S para N;3.6;2025.09.04 1800;
Aeroporto de Jacarepaguá;-22.986555;-43.366987;22.0;64.0;de N para S;3.1;2025.09.04 1700;
Rio Galeão – Tom Jobim International ;-22.8099994659;-43.2505569458;30.0;28.0;de SE para NW;3.1;2025.09.04 1800;
Guaratiba;-23.050278;-43.594722;22.2;93.6;de SW para NE;2.8;2025-10-21 11:00:00;
São Cristóvão;-22.896667;-43.221667;20.8;72.7;de SW para NE;2.5;2025-10-21 11:00:00;
Forte De Copacabana;-22.98833333;-43.19055555;23.1;77.0;de SW para NE;1.4;11/11/2022 0300;
Jacarepaguá;-22.939883;-43.402897;22.3;75.0;de SW para NE;0.9;08/12/2021 1900;
Irajá;-22.826944;-43.336944;23.3;58.2;0;0;2025-10-21 10:55:00;
Jardim Botânico;-22.972778;-43.223889;22.1;80.1;0;0;2025-10-21 11:00:00;
Barra/Riocentro;-22.977205;-43.391548;22.4;78.1;0;0;2025-10-21 11:00:00;
Santa Cruz;-22.909444;-43.684444;21.3;79.8;0;0;2025-10-21 11:00:00;
Alto da Boa Vista;-22.965833;-43.278333;19.8;65.9;0;0;2025-10-21 11:00:00;"""

print('🗑️  Limpando dados antigos...')
DadosMet.objects.all().delete()
EstacaoMet.objects.all().delete()

contador = 0
id_counter = 1

for linha in dados_api.strip().split('\n'):
    try:
        partes = linha.split(';')
        
        nome = partes[0].strip()
        lat = float(partes[1])
        lon = float(partes[2])
        temp = float(partes[3])
        umidade = float(partes[4])
        direcao = partes[5].strip()
        velocidade = float(partes[6])
        
        # Criar estação
        estacao = EstacaoMet.objects.create(
            nome=nome,
            lat=lat,
            lon=lon,
            id_e=f'MET{id_counter:03d}',
            municipio='Rio de Janeiro',
            fonte='ALERTA RIO'
        )
        
        # Criar dados com campos corretos
        agora = datetime.now()
        DadosMet.objects.create(
            estacao=estacao,
            temp=temp,
            umd=umidade,
            dire=direcao,
            vel=velocidade,
            data=agora,
            data_u=agora,
            data_aj=agora.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        contador += 1
        id_counter += 1
        print(f'✅ {nome} - Vento: {velocidade} m/s {direcao}')
        
    except Exception as e:
        print(f'❌ Erro: {e}')
        continue

print('\n' + '=' * 60)
print(f'✅ {contador} estações de vento criadas!')
print('=' * 60)