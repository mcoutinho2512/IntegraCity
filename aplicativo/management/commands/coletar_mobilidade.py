"""
Comando Django para coletar dados de mobilidade (Waze)

Uso:
    python manage.py coletar_mobilidade
    python manage.py coletar_mobilidade --cliente-id <UUID>
    python manage.py coletar_mobilidade --verbose

Para agendar via cron (a cada 15 minutos):
    */15 * * * * cd /home/administrador/integracity && python manage.py coletar_mobilidade >> /tmp/mobilidade.log 2>&1
"""

from django.core.management.base import BaseCommand
from aplicativo.models import Cliente
from aplicativo.services.integrador_waze import IntegradorWaze
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Coleta dados de mobilidade (Waze Public Traffic Feeds) de todos os clientes ativos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cliente-id',
            type=str,
            help='ID do cliente especifico (UUID)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Exibir detalhes da coleta'
        )
        parser.add_argument(
            '--calcular-nivel',
            action='store_true',
            help='Calcular nivel de mobilidade apos coleta'
        )

    def handle(self, *args, **options):
        cliente_id = options.get('cliente_id')
        verbose = options.get('verbose')
        calcular = options.get('calcular_nivel')

        self.stdout.write(self.style.NOTICE('\n' + '=' * 60))
        self.stdout.write(self.style.NOTICE('    COLETA DE DADOS DE MOBILIDADE - WAZE'))
        self.stdout.write(self.style.NOTICE('=' * 60 + '\n'))

        # Filtrar clientes
        if cliente_id:
            clientes = Cliente.objects.filter(id=cliente_id, ativo=True)
            if not clientes.exists():
                self.stdout.write(self.style.ERROR(f'Cliente {cliente_id} nao encontrado ou inativo'))
                return
        else:
            clientes = Cliente.objects.filter(ativo=True)

        total_clientes = clientes.count()

        if total_clientes == 0:
            self.stdout.write(self.style.WARNING('Nenhum cliente ativo encontrado'))
            self.stdout.write('Execute: python manage.py configurar_cliente --help')
            return

        self.stdout.write(f'Coletando dados de {total_clientes} cliente(s)...\n')

        total_sucesso = 0
        total_falhas = 0

        for cliente in clientes:
            self.stdout.write(f'\n{cliente.nome} ({cliente.cidade}/{cliente.estado})')
            self.stdout.write('-' * 40)

            # Verificar se tem feed_id configurado
            feed_id = cliente.config_apis.get('waze_feed_id') if cliente.config_apis else None

            if not feed_id:
                # Tentar inferir pela cidade
                cidade_slug = cliente.cidade.lower().replace(' ', '-')
                feed_id = IntegradorWaze.FEED_IDS.get(cidade_slug)

                if feed_id:
                    self.stdout.write(f'  Feed ID inferido: {feed_id}')
                else:
                    self.stdout.write(self.style.WARNING(
                        f'  [!] Sem feed_id configurado. Configure em config_apis.waze_feed_id'
                    ))
                    total_falhas += 1
                    continue
            else:
                if verbose:
                    self.stdout.write(f'  Feed ID configurado: {feed_id}')

            # Coletar dados
            try:
                integrador = IntegradorWaze(cliente)
                dados = integrador.coletar_dados()

                if dados:
                    total_sucesso += 1

                    self.stdout.write(self.style.SUCCESS(
                        f'  [OK] Coletado: {dados.total_jams} jams ({dados.jams_severos} severos)'
                    ))

                    if verbose:
                        self.stdout.write(f'       Alerts: {dados.total_alerts} (acidentes: {dados.acidentes_maiores + dados.acidentes_menores})')
                        self.stdout.write(f'       Irregularidades: {dados.total_irregularidades} (interditadas: {dados.vias_interditadas})')
                        if dados.velocidade_media_kmh:
                            self.stdout.write(f'       Velocidade media: {dados.velocidade_media_kmh} km/h')
                        if dados.extensao_total_km:
                            self.stdout.write(f'       Extensao congestionamentos: {dados.extensao_total_km} km')

                    # Calcular nivel se solicitado
                    if calcular:
                        nivel, detalhes = integrador.calcular_nivel_mobilidade()
                        self.stdout.write(f'  Nivel de Mobilidade: E{nivel} ({detalhes.get("nomenclatura", "?")})')
                        self.stdout.write(f'  Razao: {detalhes.get("razao", "N/A")}')
                else:
                    total_falhas += 1
                    self.stdout.write(self.style.ERROR('  [X] Falha na coleta'))

            except Exception as e:
                total_falhas += 1
                self.stdout.write(self.style.ERROR(f'  [X] Erro: {e}'))
                if verbose:
                    import traceback
                    traceback.print_exc()

        # Resumo
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.NOTICE('RESUMO'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Total de clientes: {total_clientes}')
        self.stdout.write(self.style.SUCCESS(f'Sucesso: {total_sucesso}'))

        if total_falhas > 0:
            self.stdout.write(self.style.ERROR(f'Falhas: {total_falhas}'))

        self.stdout.write('')

        # Dica para configurar feed_id
        if total_falhas > 0:
            self.stdout.write(self.style.WARNING('\nPara configurar o feed_id do Waze:'))
            self.stdout.write('  python manage.py shell')
            self.stdout.write('  >>> from aplicativo.models import Cliente')
            self.stdout.write('  >>> cliente = Cliente.objects.first()')
            self.stdout.write('  >>> cliente.config_apis["waze_feed_id"] = "18577882871"  # Rio')
            self.stdout.write('  >>> cliente.save()')
