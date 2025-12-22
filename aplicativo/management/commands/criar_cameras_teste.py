"""
Cria câmeras de teste para o sistema
"""
from django.core.management.base import BaseCommand
from aplicativo.models import Cameras
from datetime import date

class Command(BaseCommand):
    help = 'Cria câmeras de teste'

    def handle(self, *args, **options):
        cameras_teste = [
            {'id_c': 1001, 'nome': 'Túnel Rebouças - Entrada Lagoa', 'bairro': 'Lagoa', 'lat': -22.9683, 'lon': -43.2105, 'status': 'Sim'},
            {'id_c': 1002, 'nome': 'Av. Brasil - Penha', 'bairro': 'Penha', 'lat': -22.8419, 'lon': -43.2855, 'status': 'Sim'},
            {'id_c': 1003, 'nome': 'Linha Amarela - Barra', 'bairro': 'Barra da Tijuca', 'lat': -22.9964, 'lon': -43.3641, 'status': 'Sim'},
            {'id_c': 1004, 'nome': 'Centro - Presidente Vargas', 'bairro': 'Centro', 'lat': -22.9035, 'lon': -43.1896, 'status': 'Sim'},
            {'id_c': 1005, 'nome': 'Copacabana - Atlântica', 'bairro': 'Copacabana', 'lat': -22.9711, 'lon': -43.1822, 'status': 'Sim'},
            {'id_c': 1006, 'nome': 'Ipanema - Vieira Souto', 'bairro': 'Ipanema', 'lat': -22.9838, 'lon': -43.2057, 'status': 'Sim'},
            {'id_c': 1007, 'nome': 'Botafogo - Praia de Botafogo', 'bairro': 'Botafogo', 'lat': -22.9519, 'lon': -43.1822, 'status': 'Sim'},
            {'id_c': 1008, 'nome': 'Tijuca - Praça Saens Peña', 'bairro': 'Tijuca', 'lat': -22.9272, 'lon': -43.2361, 'status': 'Sim'},
            {'id_c': 1009, 'nome': 'São Conrado - Niemeyer', 'bairro': 'São Conrado', 'lat': -22.9924, 'lon': -43.2620, 'status': 'Não'},
            {'id_c': 1010, 'nome': 'Maracanã - Estádio', 'bairro': 'Maracanã', 'lat': -22.9121, 'lon': -43.2302, 'status': 'Sim'},
            {'id_c': 1011, 'nome': 'Leblon - Ataulfo de Paiva', 'bairro': 'Leblon', 'lat': -22.9844, 'lon': -43.2200, 'status': 'Sim'},
            {'id_c': 1012, 'nome': 'Flamengo - Aterro', 'bairro': 'Flamengo', 'lat': -22.9311, 'lon': -43.1729, 'status': 'Sim'},
            {'id_c': 1013, 'nome': 'Recreio - Av. das Américas', 'bairro': 'Recreio', 'lat': -23.0171, 'lon': -43.4629, 'status': 'Sim'},
            {'id_c': 1014, 'nome': 'Campo Grande - Centro', 'bairro': 'Campo Grande', 'lat': -22.9016, 'lon': -43.5578, 'status': 'Não'},
            {'id_c': 1015, 'nome': 'Jacarepaguá - Estrada dos Bandeirantes', 'bairro': 'Jacarepaguá', 'lat': -22.9320, 'lon': -43.3558, 'status': 'Sim'},
            {'id_c': 1016, 'nome': 'Santa Teresa - Largo das Neves', 'bairro': 'Santa Teresa', 'lat': -22.9155, 'lon': -43.1884, 'status': 'Sim'},
            {'id_c': 1017, 'nome': 'Bangu - Estação', 'bairro': 'Bangu', 'lat': -22.8738, 'lon': -43.4689, 'status': 'Sim'},
            {'id_c': 1018, 'nome': 'Ilha do Governador - Estrada do Galeão', 'bairro': 'Ilha do Governador', 'lat': -22.8092, 'lon': -43.2096, 'status': 'Sim'},
            {'id_c': 1019, 'nome': 'Méier - Dias da Cruz', 'bairro': 'Méier', 'lat': -22.9026, 'lon': -43.2780, 'status': 'Não'},
            {'id_c': 1020, 'nome': 'Barra - Shopping', 'bairro': 'Barra da Tijuca', 'lat': -23.0025, 'lon': -43.3195, 'status': 'Sim'},
        ]
        
        contador = 0
        for cam_data in cameras_teste:
            if not Cameras.objects.filter(id_c=cam_data['id_c']).exists():
                Cameras.objects.create(
                    id_c=cam_data['id_c'],
                    nome=cam_data['nome'],
                    bairro=cam_data['bairro'],
                    lat=str(cam_data['lat']),  # ← CONVERTER PARA STRING
                    lon=str(cam_data['lon']),  # ← CONVERTER PARA STRING
                    status=cam_data['status'],
                    criar=date.today()
                )
                contador += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ {contador} câmeras de teste criadas!'))
        self.stdout.write(f'📹 Total de câmeras no banco: {Cameras.objects.count()}')