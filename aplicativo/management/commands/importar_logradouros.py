"""
Comando Django para importar logradouros do CSV oficial do Rio de Janeiro

Fonte: Data.Rio - Logradouros.csv (132.339 registros)
URL: https://data.rio/

Uso:
    python manage.py importar_logradouros
    python manage.py importar_logradouros --arquivo /caminho/Logradouros.csv
    python manage.py importar_logradouros --apenas-arteriais
    python manage.py importar_logradouros --limpar

Para agendar importacao mensal via cron:
    0 3 1 * * cd /home/administrador/integracity && python manage.py importar_logradouros >> /tmp/logradouros.log 2>&1
"""

import csv
from django.core.management.base import BaseCommand
from django.db import models
from aplicativo.models import Logradouro
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Importa logradouros do CSV oficial do Rio de Janeiro (Data.Rio)'

    # Caminhos padrao para buscar o arquivo
    CAMINHOS_PADRAO = [
        '/mnt/user-data/uploads/Logradouros.csv',
        '/home/administrador/integracity/data/Logradouros.csv',
        '/home/administrador/Logradouros.csv',
        './Logradouros.csv',
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--arquivo',
            type=str,
            help='Caminho do arquivo CSV (busca automatica se nao especificado)'
        )
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Limpa tabela antes de importar'
        )
        parser.add_argument(
            '--apenas-arteriais',
            action='store_true',
            help='Importa apenas vias arteriais e coletoras (mais rapido)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostra detalhes de cada importacao'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Tamanho do batch para bulk_create (padrao: 1000)'
        )

    def encontrar_arquivo(self, arquivo_especificado):
        """Busca o arquivo CSV em caminhos padrao"""
        if arquivo_especificado:
            if os.path.exists(arquivo_especificado):
                return arquivo_especificado
            self.stdout.write(self.style.ERROR(f'Arquivo nao encontrado: {arquivo_especificado}'))
            return None

        for caminho in self.CAMINHOS_PADRAO:
            if os.path.exists(caminho):
                return caminho

        return None

    def handle(self, *args, **options):
        arquivo = self.encontrar_arquivo(options.get('arquivo'))
        limpar = options.get('limpar')
        apenas_arteriais = options.get('apenas_arteriais')
        verbose = options.get('verbose')
        batch_size = options.get('batch_size')

        self.stdout.write(self.style.NOTICE('\n' + '=' * 60))
        self.stdout.write(self.style.NOTICE('    IMPORTACAO DE LOGRADOUROS - DATA.RIO'))
        self.stdout.write(self.style.NOTICE('=' * 60 + '\n'))

        if not arquivo:
            self.stdout.write(self.style.ERROR('Arquivo Logradouros.csv nao encontrado!'))
            self.stdout.write('\nCaminhos verificados:')
            for caminho in self.CAMINHOS_PADRAO:
                self.stdout.write(f'  - {caminho}')
            self.stdout.write('\nBaixe o arquivo em: https://data.rio/')
            self.stdout.write('Ou especifique o caminho: python manage.py importar_logradouros --arquivo /caminho/Logradouros.csv')
            return

        self.stdout.write(f'Arquivo encontrado: {arquivo}')

        if limpar:
            self.stdout.write('\nLimpando tabela de logradouros...')
            count = Logradouro.objects.count()
            Logradouro.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'  Removidos {count:,} registros'))

        self.stdout.write(f'\nImportando logradouros...\n')

        total_linhas = 0
        total_importados = 0
        total_atualizados = 0
        total_erros = 0
        total_ignorados = 0

        # Contar linhas primeiro para barra de progresso
        with open(arquivo, 'r', encoding='utf-8-sig') as f:
            total_linhas_arquivo = sum(1 for _ in f) - 1  # -1 para header

        self.stdout.write(f'Total de linhas no arquivo: {total_linhas_arquivo:,}')

        batch = []

        with open(arquivo, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                total_linhas += 1

                # Filtro: apenas arteriais?
                if apenas_arteriais:
                    hierarquia = row.get('hierarquia', '').strip()
                    if hierarquia not in ['Arterial primária', 'Arterial secundária', 'Coletora']:
                        total_ignorados += 1
                        continue

                try:
                    # Parsing de campos
                    cod_trecho = int(row['cod_trecho'])

                    # Data de ultima edicao
                    ultima_edicao = None
                    if row.get('last_edited_date'):
                        try:
                            # Formato: 2025/10/21 22:45:38+00
                            data_str = row['last_edited_date'].split('+')[0]
                            ultima_edicao = datetime.strptime(data_str, '%Y/%m/%d %H:%M:%S')
                        except Exception:
                            pass

                    # Helper para converter inteiros com seguranca
                    def safe_int(val):
                        if not val or val.strip() == '':
                            return None
                        try:
                            return int(float(val))
                        except (ValueError, TypeError):
                            return None

                    # Criar objeto Logradouro
                    logradouro = Logradouro(
                        cod_trecho=cod_trecho,
                        cod_logradouro=row.get('cl', '').strip(),
                        tipo_abreviado=row.get('tipo_logra_abr', '').strip(),
                        tipo_extenso=row.get('tipo_logra_ext', '').strip(),
                        nome_parcial=row.get('nome_parcial', '').strip(),
                        nome_completo=row.get('completo', '').strip(),
                        nome_mapa=row.get('nome_mapa', '').strip(),
                        bairro=row.get('bairro', '').strip() or None,
                        cod_bairro=safe_int(row.get('cod_bairro')),
                        hierarquia=row.get('hierarquia', '').strip() or None,
                        sentido_unico=row.get('oneway', '').strip() or None,
                        velocidade_regulamentada=safe_int(row.get('velocidade_regulamentada')),
                        tipo_trecho=row.get('tipo_trecho', '').strip() or None,
                        num_par_inicio=safe_int(row.get('np_ini_par')),
                        num_par_fim=safe_int(row.get('np_fin_par')),
                        num_impar_inicio=safe_int(row.get('np_ini_imp')),
                        num_impar_fim=safe_int(row.get('np_fin_imp')),
                        objectid=safe_int(row.get('objectid')),
                        ultima_edicao=ultima_edicao,
                    )

                    batch.append(logradouro)
                    total_importados += 1

                    if verbose and total_importados % 1000 == 0:
                        self.stdout.write(f'  Processados: {total_importados:,}')

                    # Salvar batch
                    if len(batch) >= batch_size:
                        self._salvar_batch(batch)
                        batch = []

                except Exception as e:
                    total_erros += 1
                    if total_erros <= 10:  # Mostrar apenas primeiros erros
                        logger.error(f'Erro na linha {total_linhas}: {e}')
                        if verbose:
                            self.stdout.write(self.style.ERROR(f'  Erro linha {total_linhas}: {e}'))

        # Salvar batch restante
        if batch:
            self._salvar_batch(batch)

        # Resumo
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('IMPORTACAO CONCLUIDA'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Total de linhas no CSV: {total_linhas:,}')
        self.stdout.write(self.style.SUCCESS(f'  Logradouros importados: {total_importados:,}'))
        if total_ignorados > 0:
            self.stdout.write(f'  Ignorados (filtro arteriais): {total_ignorados:,}')
        if total_erros > 0:
            self.stdout.write(self.style.WARNING(f'  Erros: {total_erros}'))

        # Estatisticas do banco
        self._mostrar_estatisticas()

    def _salvar_batch(self, batch):
        """Salva batch usando update_or_create para suportar atualizacoes"""
        for logradouro in batch:
            Logradouro.objects.update_or_create(
                cod_trecho=logradouro.cod_trecho,
                defaults={
                    'cod_logradouro': logradouro.cod_logradouro,
                    'tipo_abreviado': logradouro.tipo_abreviado,
                    'tipo_extenso': logradouro.tipo_extenso,
                    'nome_parcial': logradouro.nome_parcial,
                    'nome_completo': logradouro.nome_completo,
                    'nome_mapa': logradouro.nome_mapa,
                    'bairro': logradouro.bairro,
                    'cod_bairro': logradouro.cod_bairro,
                    'hierarquia': logradouro.hierarquia,
                    'sentido_unico': logradouro.sentido_unico,
                    'velocidade_regulamentada': logradouro.velocidade_regulamentada,
                    'tipo_trecho': logradouro.tipo_trecho,
                    'num_par_inicio': logradouro.num_par_inicio,
                    'num_par_fim': logradouro.num_par_fim,
                    'num_impar_inicio': logradouro.num_impar_inicio,
                    'num_impar_fim': logradouro.num_impar_fim,
                    'objectid': logradouro.objectid,
                    'ultima_edicao': logradouro.ultima_edicao,
                }
            )

    def _mostrar_estatisticas(self):
        """Mostra estatisticas dos logradouros importados"""
        self.stdout.write('\n' + '-' * 40)
        self.stdout.write('ESTATISTICAS DO BANCO:')
        self.stdout.write('-' * 40)

        total = Logradouro.objects.count()
        self.stdout.write(f'  Total de logradouros: {total:,}')

        # Por tipo de via
        self.stdout.write('\n  Por tipo de via:')
        tipos = Logradouro.objects.values('tipo_extenso').annotate(
            total=models.Count('cod_trecho')
        ).order_by('-total')[:10]

        for tipo in tipos:
            self.stdout.write(f"    {tipo['tipo_extenso']}: {tipo['total']:,}")

        # Por hierarquia
        self.stdout.write('\n  Por hierarquia:')
        hierarquias = Logradouro.objects.exclude(
            hierarquia__isnull=True
        ).values('hierarquia').annotate(
            total=models.Count('cod_trecho')
        ).order_by('-total')

        for h in hierarquias:
            self.stdout.write(f"    {h['hierarquia']}: {h['total']:,}")

        # Com velocidade regulamentada
        com_velocidade = Logradouro.objects.exclude(
            velocidade_regulamentada__isnull=True
        ).count()
        self.stdout.write(f'\n  Com velocidade regulamentada: {com_velocidade:,}')

        # Por bairro (top 10)
        self.stdout.write('\n  Top 10 bairros:')
        bairros = Logradouro.objects.exclude(
            bairro__isnull=True
        ).values('bairro').annotate(
            total=models.Count('cod_trecho')
        ).order_by('-total')[:10]

        for b in bairros:
            self.stdout.write(f"    {b['bairro']}: {b['total']:,}")

        self.stdout.write('')
