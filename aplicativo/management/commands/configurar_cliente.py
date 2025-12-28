"""
Comando Django para configurar um novo cliente (cidade) no sistema IntegraCity

Uso:
    python manage.py configurar_cliente \
        --nome "Prefeitura de Niterói" \
        --cidade "Niterói" \
        --estado "RJ" \
        --lat -22.8833 \
        --lon -43.1036

Opções:
    --plano: basico, profissional (default), enterprise
    --raio-estacoes: raio de busca de estações INMET em km (default: 100)
"""

from django.core.management.base import BaseCommand, CommandError
from aplicativo.models import Cliente
from aplicativo.services.integrador_inmet import IntegradorINMET


class Command(BaseCommand):
    help = 'Configura um novo cliente (cidade) no sistema IntegraCity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nome',
            type=str,
            required=True,
            help='Nome do cliente (ex: "Prefeitura de Niterói")'
        )
        parser.add_argument(
            '--cidade',
            type=str,
            required=True,
            help='Nome da cidade'
        )
        parser.add_argument(
            '--estado',
            type=str,
            required=True,
            help='Sigla do estado (ex: RJ)'
        )
        parser.add_argument(
            '--lat',
            type=float,
            required=True,
            help='Latitude (ex: -22.8833)'
        )
        parser.add_argument(
            '--lon',
            type=float,
            required=True,
            help='Longitude (ex: -43.1036)'
        )
        parser.add_argument(
            '--plano',
            type=str,
            default='profissional',
            choices=['basico', 'profissional', 'enterprise'],
            help='Plano contratado'
        )
        parser.add_argument(
            '--raio-estacoes',
            type=int,
            default=100,
            help='Raio de busca de estações INMET em km (padrão: 100)'
        )
        parser.add_argument(
            '--responsavel',
            type=str,
            default='',
            help='Nome do responsável técnico'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='',
            help='Email de contato'
        )
        parser.add_argument(
            '--telefone',
            type=str,
            default='',
            help='Telefone de contato'
        )

    def handle(self, *args, **options):
        nome = options['nome']
        cidade = options['cidade']
        estado = options['estado'].upper()
        lat = options['lat']
        lon = options['lon']
        plano = options['plano']
        raio = options['raio_estacoes']

        # Validar estado
        if len(estado) != 2:
            raise CommandError('Estado deve ter 2 caracteres (ex: RJ)')

        # Validar coordenadas (Brasil)
        if not (-35 <= lat <= 6):
            self.stdout.write(self.style.WARNING(
                f'Latitude {lat} pode estar fora do Brasil (-35 a 6)'
            ))
        if not (-74 <= lon <= -32):
            self.stdout.write(self.style.WARNING(
                f'Longitude {lon} pode estar fora do Brasil (-74 a -32)'
            ))

        # Criar slug a partir da cidade
        import re
        from django.utils.text import slugify
        slug = slugify(cidade)

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.NOTICE('CONFIGURAÇÃO DE NOVO CLIENTE'))
        self.stdout.write('=' * 60 + '\n')

        self.stdout.write(f'Nome: {nome}')
        self.stdout.write(f'Cidade: {cidade}/{estado}')
        self.stdout.write(f'Coordenadas: {lat}, {lon}')
        self.stdout.write(f'Plano: {plano}')
        self.stdout.write(f'Slug: {slug}')

        # Verificar se já existe
        if Cliente.objects.filter(slug=slug).exists():
            cliente_existente = Cliente.objects.get(slug=slug)
            self.stdout.write(self.style.WARNING(
                f'\nCliente com slug "{slug}" já existe (ID: {cliente_existente.id})'
            ))
            self.stdout.write('Atualizando estações meteorológicas...\n')
            cliente = cliente_existente
        else:
            # Criar cliente
            cliente = Cliente.objects.create(
                nome=nome,
                slug=slug,
                cidade=cidade,
                estado=estado,
                latitude=lat,
                longitude=lon,
                plano=plano,
                responsavel_nome=options.get('responsavel', ''),
                responsavel_email=options.get('email', ''),
                responsavel_telefone=options.get('telefone', ''),
                ativo=True,
            )

            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Cliente criado: {cliente.nome}'
            ))
            self.stdout.write(f'  ID: {cliente.id}')

        # Buscar e cadastrar estações INMET
        self.stdout.write(self.style.NOTICE(
            f'\nBuscando estações INMET (raio: {raio}km)...'
        ))

        integrador = IntegradorINMET(cliente)
        estacoes_proximas = integrador.buscar_estacoes_proximas(raio_km=raio)

        if estacoes_proximas:
            self.stdout.write(f'Encontradas {len(estacoes_proximas)} estações:')
            for i, est in enumerate(estacoes_proximas[:10]):
                self.stdout.write(f'  {i+1}. {est["nome"]} ({est["codigo"]}) - {est["distancia"]:.1f}km')

        num_estacoes = integrador.cadastrar_estacoes(raio_km=raio, max_estacoes=5)

        if num_estacoes > 0:
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ {num_estacoes} estação(ões) cadastrada(s)'
            ))

            # Listar estações cadastradas
            estacoes = cliente.estacoes.all().order_by('distancia_km')
            for est in estacoes:
                principal = " [PRINCIPAL]" if est.principal else ""
                self.stdout.write(
                    f'  - {est.nome} ({est.codigo_inmet}) - {est.distancia_km}km{principal}'
                )
        else:
            self.stdout.write(self.style.WARNING(
                '⚠ Nenhuma estação encontrada ou cadastrada'
            ))

        # Tentar coletar dados
        self.stdout.write(self.style.NOTICE('\nColetando dados meteorológicos...'))
        sucesso, total = integrador.coletar_todas_estacoes()

        if sucesso > 0:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Dados coletados de {sucesso}/{total} estação(ões)'
            ))

            # Mostrar resumo dos dados
            resumo = integrador.obter_resumo_meteorologico()
            nivel = resumo['nivel_calculado']
            detalhes = resumo['detalhes_nivel']

            self.stdout.write(f'\nNível Meteorológico: E{nivel}')
            if 'temperatura' in detalhes and detalhes['temperatura']:
                self.stdout.write(f'  Temperatura: {detalhes["temperatura"]:.1f}°C')
            if 'umidade' in detalhes and detalhes['umidade']:
                self.stdout.write(f'  Umidade: {detalhes["umidade"]:.0f}%')
            if 'chuva_mm_h' in detalhes:
                self.stdout.write(f'  Precipitação: {detalhes["chuva_mm_h"]:.1f}mm/h')
            if 'vento_kmh' in detalhes:
                self.stdout.write(f'  Vento: {detalhes["vento_kmh"]:.1f}km/h')

        else:
            self.stdout.write(self.style.WARNING(
                '⚠ Não foi possível coletar dados'
            ))

        # Resumo final
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✓ CONFIGURAÇÃO CONCLUÍDA!'))
        self.stdout.write('=' * 60)

        self.stdout.write(f'''
Cliente: {cliente.nome}
ID: {cliente.id}
Slug: {cliente.slug}
Estações: {cliente.estacoes.count()}

Próximos passos:
1. Configure o cron para coletar dados a cada hora:
   0 * * * * cd /home/administrador/integracity && ./venv/bin/python manage.py coletar_meteorologia

2. Acesse o dashboard:
   http://10.50.72.239/integracity/meteorologia/

3. Verifique a matriz decisória:
   http://10.50.72.239/integracity/matriz/
''')
