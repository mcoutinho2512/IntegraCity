"""
Comando Django para coletar dados meteorológicos de todos os clientes

Uso:
    python manage.py coletar_meteorologia

Opções:
    --cliente-id: UUID do cliente específico (opcional)
    --verbose: Mostrar detalhes da coleta

Cron sugerido (a cada hora):
    0 * * * * cd /home/administrador/integracity && ./venv/bin/python manage.py coletar_meteorologia >> /tmp/meteorologia.log 2>&1
"""

from django.core.management.base import BaseCommand
from aplicativo.models import Cliente
from aplicativo.services.integrador_inmet import IntegradorINMET
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Coleta dados meteorológicos de todos os clientes ativos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cliente-id',
            type=str,
            help='ID (UUID) do cliente específico'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar detalhes da coleta'
        )
        parser.add_argument(
            '--calcular-nivel',
            action='store_true',
            help='Calcular e mostrar nível meteorológico após coleta'
        )

    def handle(self, *args, **options):
        cliente_id = options.get('cliente_id')
        verbose = options.get('verbose', False)
        calcular = options.get('calcular_nivel', False)

        if cliente_id:
            clientes = Cliente.objects.filter(id=cliente_id, ativo=True)
            if not clientes.exists():
                self.stdout.write(self.style.ERROR(
                    f'Cliente não encontrado: {cliente_id}'
                ))
                return
        else:
            clientes = Cliente.objects.filter(ativo=True)

        total_clientes = clientes.count()

        if total_clientes == 0:
            self.stdout.write(self.style.WARNING(
                'Nenhum cliente ativo encontrado. Configure um cliente primeiro:'
            ))
            self.stdout.write('  python manage.py configurar_cliente --help')
            return

        self.stdout.write(f'Coletando dados de {total_clientes} cliente(s)...\n')

        total_sucesso = 0
        total_estacoes = 0

        for cliente in clientes:
            self.stdout.write(f'Cliente: {cliente.nome} ({cliente.cidade}/{cliente.estado})')

            integrador = IntegradorINMET(cliente)
            sucesso, total = integrador.coletar_todas_estacoes()

            total_sucesso += sucesso
            total_estacoes += total

            if sucesso > 0:
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ {sucesso}/{total} estação(ões)'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'  ⚠ Nenhum dado coletado ({total} estações)'
                ))

            # Mostrar detalhes se verbose
            if verbose and sucesso > 0:
                resumo = integrador.obter_resumo_meteorologico()
                for est in resumo['estacoes']:
                    if est['dados']:
                        dados = est['dados']
                        self.stdout.write(
                            f'    {est["nome"]}: '
                            f'{dados.get("temperatura", "-")}°C, '
                            f'{dados.get("umidade", "-")}%, '
                            f'Chuva: {dados.get("chuva_mm", 0):.1f}mm, '
                            f'Vento: {dados.get("vento_kmh", 0):.1f}km/h'
                        )

            # Calcular nível se solicitado
            if calcular:
                nivel, detalhes = integrador.calcular_nivel_meteorologia()

                # Cores para níveis
                cores = {
                    1: self.style.SUCCESS,
                    2: self.style.HTTP_INFO,
                    3: self.style.WARNING,
                    4: self.style.ERROR,
                    5: self.style.ERROR,
                }

                estilo = cores.get(nivel, self.style.NOTICE)
                self.stdout.write(estilo(
                    f'  Nível Meteorológico: E{nivel} - {detalhes.get("razao", "Normal")}'
                ))

            self.stdout.write('')  # Linha em branco

        # Resumo final
        self.stdout.write('=' * 50)
        if total_sucesso > 0:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Coleta finalizada: {total_sucesso}/{total_estacoes} estações'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'⚠ Coleta com problemas: {total_sucesso}/{total_estacoes} estações'
            ))

        self.stdout.write(f'Clientes processados: {total_clientes}')
