"""
Comando Django para importar matriz decisoria inicial v3.5

Uso:
    python manage.py importar_matriz
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from aplicativo.models import MatrizDecisoria, AcaoRecomendada, AgenciaResponsavel

User = get_user_model()


class Command(BaseCommand):
    help = 'Importa matriz decisoria inicial v3.5'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forca a recriacao da matriz mesmo se ja existir',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('\n' + '=' * 60))
        self.stdout.write(self.style.NOTICE('IMPORTACAO DA MATRIZ DECISORIA'))
        self.stdout.write(self.style.NOTICE('=' * 60 + '\n'))

        # Buscar ou criar usuario sistema
        sistema_user, user_created = User.objects.get_or_create(
            username='sistema',
            defaults={
                'first_name': 'Sistema',
                'last_name': 'Automatico',
                'email': 'sistema@integracity.local',
                'is_active': False,
            }
        )

        if user_created:
            self.stdout.write(self.style.SUCCESS('Usuario "sistema" criado'))
        else:
            self.stdout.write('Usuario "sistema" ja existe')

        # Verificar se matriz ja existe
        matriz_existente = MatrizDecisoria.objects.filter(versao='3.5').first()

        if matriz_existente and not options['force']:
            self.stdout.write(self.style.WARNING(
                f'\nMatriz v3.5 ja existe (ID: {matriz_existente.id})'
            ))
            self.stdout.write('Use --force para recriar')
            return

        if matriz_existente and options['force']:
            self.stdout.write(self.style.WARNING('Removendo matriz existente...'))
            matriz_existente.delete()

        # Criar matriz
        self.stdout.write('\nCriando Matriz v3.5...')

        matriz = MatrizDecisoria.objects.create(
            versao='3.5',
            nome='Matriz Decisoria v3.5',
            descricao='''Matriz Decisoria para analise do estagio operacional da cidade.
Baseada no padrao COR Rio: https://cor.rio/estagios-operacionais-da-cidade/

4 grupos de criterios:
- Grupo 1: Meteorologia (Peso 2.0)
- Grupo 2: Incidentes/Ocorrencias (Peso 2.0)
- Grupo 3: Mobilidade (Peso 1.0)
- Grupo 4: Eventos (Peso 1.0)

Estagios Operacionais (1-5):
1 - Normal       - Sem ocorrencias significativas
2 - Mobilizacao  - Risco de eventos de alto impacto
3 - Atencao      - Impactos ja ocorrendo em alguma regiao
4 - Alerta       - Ocorrencias graves ou multiplos problemas
5 - Crise        - Multiplos danos excedem capacidade de resposta''',
            status='publicada',
            ativa=True,
            peso_meteorologia=2.0,
            peso_incidentes=2.0,
            peso_mobilidade=1.0,
            peso_eventos=1.0,
            config_grupo1={
                'nome': 'Meteorologia',
                'fontes': ['Alerta Rio', 'GeoRio/LHASA'],
                'criterios': [
                    'Acumulado de chuva (mm)',
                    'Velocidade dos ventos (km/h)',
                    'Risco de deslizamentos',
                    'Indice de calor'
                ],
            },
            config_grupo2={
                'nome': 'Incidentes/Ocorrencias',
                'horas_retro': 24,
                'tabela_niveis': {
                    'baixas': {'n0': 9, 'n1': 14, 'n2': 19, 'n3': 29, 'n4': 39, 'n5': 49, 'n6': 50},
                    'medias': {'n0': 4, 'n1': 7, 'n2': 9, 'n3': 14, 'n4': 19, 'n5': 29, 'n6': 30},
                    'altas': {'n0': 0, 'n1': 1, 'n2': 2, 'n3': 4, 'n4': 6, 'n5': 9, 'n6': 10},
                    'criticas': {'n6': 1},
                },
            },
            config_grupo3={
                'nome': 'Mobilidade',
                'fontes': ['WAZE', 'CIMU'],
                'criterios': [
                    'Percentual de transito acima do normal',
                    'Modos CIMU (amarelo/vermelho)',
                    'Interdicoes de vias protocolares',
                    'Acionamento de sirenes'
                ],
            },
            config_grupo4={
                'nome': 'Eventos',
                'criterios': [
                    'Eventos de baixa criticidade',
                    'Eventos de media criticidade',
                    'Eventos de alta criticidade',
                    'Eventos de muito alta criticidade'
                ],
            },
            created_by=sistema_user,
        )

        self.stdout.write(self.style.SUCCESS(f'Matriz criada: {matriz}'))

        # Criar acoes recomendadas
        self.stdout.write('\nCriando acoes recomendadas...')

        # Ações recomendadas para os 5 estágios do COR Rio
        acoes_data = [
            # ESTÁGIO 1 - NORMAL
            {
                'nivel_min': 1,
                'nivel_max': 1,
                'titulo': 'NORMAL - Monitoramento Padrao',
                'descricao': 'Manter monitoramento padrao da cidade. Acompanhar indicadores meteorologicos e de transito. Sem alertas ativos.',
                'prioridade': 'baixa',
                'prazo': None,
                'ordem': 1,
            },
            # ESTÁGIO 2 - MOBILIZAÇÃO
            {
                'nivel_min': 2,
                'nivel_max': 2,
                'titulo': 'MOBILIZACAO - Aumentar Vigilancia',
                'descricao': 'Aumentar frequencia de monitoramento. Verificar previsoes meteorologicas. Alertar equipes de prontidao.',
                'prioridade': 'baixa',
                'prazo': 12,
                'ordem': 1,
            },
            {
                'nivel_min': 2,
                'nivel_max': 2,
                'titulo': 'MOBILIZACAO - Preparar Recursos',
                'descricao': 'Verificar disponibilidade de recursos. Confirmar comunicacao com agencias. Preparar planos de contingencia.',
                'prioridade': 'baixa',
                'prazo': 8,
                'ordem': 2,
            },
            # ESTÁGIO 3 - ATENÇÃO
            {
                'nivel_min': 3,
                'nivel_max': 3,
                'titulo': 'ATENCAO - Ativar Monitoramento Intensivo',
                'descricao': 'Monitoramento intensivo de todas as fontes. Impactos ja ocorrendo em alguma regiao. Acionar equipes de apoio.',
                'prioridade': 'media',
                'prazo': 6,
                'ordem': 1,
            },
            {
                'nivel_min': 3,
                'nivel_max': 3,
                'titulo': 'ATENCAO - Verificar POPs de Contingencia',
                'descricao': 'Revisar procedimentos operacionais padrao. Garantir comunicacao com todas as agencias. Preparar recursos de emergencia.',
                'prioridade': 'media',
                'prazo': 4,
                'ordem': 2,
            },
            # ESTÁGIO 4 - ALERTA
            {
                'nivel_min': 4,
                'nivel_max': 4,
                'titulo': 'ALERTA - Acionar Equipes de Campo',
                'descricao': 'Mobilizar equipes de campo em areas criticas. Ativar sala de situacao. Coordenar com agencias externas.',
                'prioridade': 'alta',
                'prazo': 2,
                'ordem': 1,
            },
            {
                'nivel_min': 4,
                'nivel_max': 4,
                'titulo': 'ALERTA - Comunicacao com a Populacao',
                'descricao': 'Emitir comunicados oficiais. Ativar canais de comunicacao de emergencia. Orientar populacao sobre areas de risco.',
                'prioridade': 'alta',
                'prazo': 2,
                'ordem': 2,
            },
            # ESTÁGIO 5 - CRISE
            {
                'nivel_min': 5,
                'nivel_max': 5,
                'titulo': 'CRISE - Ativar Gabinete de Crise',
                'descricao': 'Ativar gabinete de crise completo. Convocar gestores de todas as agencias. Operacao 24 horas. Multiplos danos excedem capacidade normal.',
                'prioridade': 'critica',
                'prazo': 1,
                'ordem': 1,
            },
            {
                'nivel_min': 5,
                'nivel_max': 5,
                'titulo': 'CRISE - Coordenacao Interagencias',
                'descricao': 'Estabelecer comando unificado. Distribuir recursos de forma coordenada. Priorizar areas de maior risco.',
                'prioridade': 'critica',
                'prazo': 1,
                'ordem': 2,
            },
            {
                'nivel_min': 5,
                'nivel_max': 5,
                'titulo': 'CRISE - Solicitar Apoio Externo',
                'descricao': 'Acionar Defesa Civil Estadual se necessario. Solicitar recursos extras. Avaliar medidas extraordinarias.',
                'prioridade': 'critica',
                'prazo': 1,
                'ordem': 3,
            },
        ]

        for acao_data in acoes_data:
            acao = AcaoRecomendada.objects.create(
                matriz=matriz,
                nivel_minimo=acao_data['nivel_min'],
                nivel_maximo=acao_data['nivel_max'],
                titulo=acao_data['titulo'],
                descricao=acao_data['descricao'],
                prioridade_automatica=acao_data['prioridade'],
                prazo_horas=acao_data['prazo'],
                ordem=acao_data['ordem'],
            )
            self.stdout.write(f'  - {acao.titulo}')

        # Vincular agencias existentes as acoes de crise
        self.stdout.write('\nVinculando agencias as acoes de crise...')

        agencias = AgenciaResponsavel.objects.filter(ativa=True)
        acoes_crise = AcaoRecomendada.objects.filter(
            matriz=matriz,
            nivel_minimo__gte=4
        )

        for acao in acoes_crise:
            acao.agencias.set(agencias)
            self.stdout.write(f'  - {acao.titulo}: {agencias.count()} agencias vinculadas')

        # Resumo
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('IMPORTACAO CONCLUIDA COM SUCESSO!'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'''
Matriz: {matriz.nome} (v{matriz.versao})
Status: {matriz.get_status_display()}
Ativa: {'Sim' if matriz.ativa else 'Nao'}

Pesos:
  - Meteorologia: {matriz.peso_meteorologia}
  - Incidentes: {matriz.peso_incidentes}
  - Mobilidade: {matriz.peso_mobilidade}
  - Eventos: {matriz.peso_eventos}

Acoes Recomendadas: {AcaoRecomendada.objects.filter(matriz=matriz).count()}
Agencias Vinculadas: {agencias.count()}

Acesse: /integracity/matriz/
''')
