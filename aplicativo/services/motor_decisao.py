"""
Motor de Decisão - Matriz Decisória IntegraCity
==============================================

Calcula o estágio operacional da cidade baseado em:
- Grupo 1: Meteorologia (Peso 2.0)
- Grupo 2: Incidentes/Ocorrências (Peso 2.0)
- Grupo 3: Mobilidade (Peso 1.0)
- Grupo 4: Eventos (Peso 1.0)

Níveis resultantes (1-5) - Padrão COR Rio:
https://cor.rio/estagios-operacionais-da-cidade/

- 1: Normal       - Sem ocorrências significativas
- 2: Mobilização  - Risco de eventos de alto impacto
- 3: Atenção      - Impactos já ocorrendo em alguma região
- 4: Alerta       - Ocorrências graves ou múltiplos problemas
- 5: Crise        - Múltiplos danos excedem capacidade de resposta
"""

from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
import logging

logger = logging.getLogger(__name__)


class MotorDecisao:
    """
    Motor de cálculo do estágio operacional da cidade
    baseado na Matriz Decisória IntegraCity
    """

    def __init__(self, matriz=None):
        """
        Inicializa o motor com uma matriz específica ou a ativa

        Args:
            matriz: Instância de MatrizDecisoria (opcional)
        """
        # Import local para evitar circular import
        from ..models import MatrizDecisoria

        if matriz:
            self.matriz = matriz
        else:
            # Buscar matriz ativa
            self.matriz = MatrizDecisoria.objects.filter(
                ativa=True,
                status='publicada'
            ).first()

            if not self.matriz:
                raise ValueError("Nenhuma matriz decisória ativa encontrada. Configure uma matriz primeiro.")

    def calcular_nivel_incidentes(self, horas_retro: int = 24) -> Tuple[int, Dict]:
        """
        Calcula nível do Grupo 2 (Incidentes) baseado em ocorrências

        Regras conforme matriz de decisão:
        - Conta ocorrências das últimas N horas (padrão 24h)
        - Separa por prioridade (baixa, média, alta, crítica)
        - Aplica tabela de níveis progressivos

        Args:
            horas_retro: Horas retroativas para análise (padrão 24)

        Returns:
            Tuple[int, Dict]: (nível calculado, detalhes do cálculo)
        """
        from ..models import OcorrenciaGerenciada

        limite = timezone.now() - timedelta(hours=horas_retro)

        ocorrencias = OcorrenciaGerenciada.objects.filter(
            data_abertura__gte=limite,
            status__in=['aberta', 'em_andamento', 'aguardando']
        )

        # Contar por prioridade
        stats = ocorrencias.aggregate(
            baixas=Count('id', filter=Q(prioridade='baixa')),
            medias=Count('id', filter=Q(prioridade='media')),
            altas=Count('id', filter=Q(prioridade='alta')),
            criticas=Count('id', filter=Q(prioridade='critica')),
        )

        baixas = stats['baixas'] or 0
        medias = stats['medias'] or 0
        altas = stats['altas'] or 0
        criticas = stats['criticas'] or 0

        # Aplicar regras - prioridade para mais críticas (níveis 1-5 padrão COR Rio)
        nivel = 1  # Normal por padrão
        razoes = []

        # MUITO ALTAS (Críticas) - maior prioridade, imediatamente nível 5 (Crise)
        if criticas >= 1:
            nivel = 5
            razoes.append(f"{criticas} ocorrência(s) CRÍTICA(S) - Nível CRISE ativado")

        # ALTAS
        if altas >= 6:
            nivel = max(nivel, 5)  # Crise
            razoes.append(f"{altas} ocorrências ALTAS (>=6)")
        elif altas >= 4:
            nivel = max(nivel, 4)  # Alerta
            razoes.append(f"{altas} ocorrências ALTAS (4-5)")
        elif altas >= 2:
            nivel = max(nivel, 3)  # Atenção
            razoes.append(f"{altas} ocorrências ALTAS (2-3)")
        elif altas == 1:
            nivel = max(nivel, 2)  # Mobilização
            razoes.append(f"{altas} ocorrência ALTA")

        # MÉDIAS
        if medias >= 25:
            nivel = max(nivel, 5)  # Crise
            razoes.append(f"{medias} ocorrências MÉDIAS (>=25)")
        elif medias >= 18:
            nivel = max(nivel, 4)  # Alerta
            razoes.append(f"{medias} ocorrências MÉDIAS (18-24)")
        elif medias >= 12:
            nivel = max(nivel, 3)  # Atenção
            razoes.append(f"{medias} ocorrências MÉDIAS (12-17)")
        elif medias >= 6:
            nivel = max(nivel, 2)  # Mobilização
            razoes.append(f"{medias} ocorrências MÉDIAS (6-11)")

        # BAIXAS
        if baixas >= 40:
            nivel = max(nivel, 5)  # Crise
            razoes.append(f"{baixas} ocorrências BAIXAS (>=40)")
        elif baixas >= 30:
            nivel = max(nivel, 4)  # Alerta
            razoes.append(f"{baixas} ocorrências BAIXAS (30-39)")
        elif baixas >= 20:
            nivel = max(nivel, 3)  # Atenção
            razoes.append(f"{baixas} ocorrências BAIXAS (20-29)")
        elif baixas >= 10:
            nivel = max(nivel, 2)  # Mobilização
            razoes.append(f"{baixas} ocorrências BAIXAS (10-19)")

        detalhes = {
            'baixas': baixas,
            'medias': medias,
            'altas': altas,
            'criticas': criticas,
            'total': baixas + medias + altas + criticas,
            'horas_analisadas': horas_retro,
            'nivel_calculado': nivel,
            'razao': '; '.join(razoes) if razoes else 'Nível normal - quantidade de ocorrências dentro do esperado',
        }

        logger.info(f"Grupo 2 (Incidentes): Nível {nivel} - Total: {detalhes['total']} ocorrências")

        return nivel, detalhes

    def calcular_nivel_cidade(
        self,
        nivel_meteo: int = None,
        nivel_mob: int = 0,
        nivel_eventos: int = 0,
        usuario=None,
        dados_extras: Optional[Dict] = None
    ):
        """
        Calcula nível final da cidade aplicando pesos aos grupos

        Fórmula:
        Nível = (G1*P1 + G2*P2 + G3*P3 + G4*P4) / (P1+P2+P3+P4)

        Args:
            nivel_meteo: Nível do Grupo 1 (Meteorologia) - None = calcular automático via INMET
            nivel_mob: Nível do Grupo 3 (Mobilidade) - padrão 0
            nivel_eventos: Nível do Grupo 4 (Eventos) - padrão 0
            usuario: Usuário que solicitou o cálculo
            dados_extras: Dados adicionais para registro

        Returns:
            EstagioOperacional: Objeto com resultado do cálculo
        """
        from ..models import EstagioOperacional, AcaoRecomendada, Cliente

        # Calcular nível de incidentes automaticamente
        nivel_incidentes, detalhes_incidentes = self.calcular_nivel_incidentes()

        # ========================================
        # GRUPO 1 - METEOROLOGIA (AUTOMÁTICO VIA INMET)
        # ========================================
        detalhes_meteorologia = {}

        if nivel_meteo is None or nivel_meteo == 0:
            # Calcular automaticamente via INMET
            try:
                from .integrador_inmet import IntegradorINMET

                # Buscar cliente ativo (primeiro encontrado)
                cliente = Cliente.objects.filter(ativo=True).first()

                if cliente:
                    integrador = IntegradorINMET(cliente)
                    nivel_meteo, detalhes_meteorologia = integrador.calcular_nivel_meteorologia()
                    detalhes_meteorologia['fonte'] = 'INMET'
                    detalhes_meteorologia['automatico'] = True
                    logger.info(f"Meteorologia via INMET: E{nivel_meteo}")
                else:
                    nivel_meteo = 1
                    detalhes_meteorologia = {
                        'nivel': 1,
                        'fonte': 'default',
                        'erro': 'Nenhum cliente configurado',
                        'razao': 'Configure um cliente para ativar integração INMET',
                    }
                    logger.warning("Meteorologia: Nenhum cliente configurado")

            except ImportError as e:
                nivel_meteo = 1
                detalhes_meteorologia = {
                    'nivel': 1,
                    'fonte': 'default',
                    'erro': f'Módulo não disponível: {e}',
                }
                logger.error(f"Erro ao importar IntegradorINMET: {e}")

            except Exception as e:
                nivel_meteo = 1
                detalhes_meteorologia = {
                    'nivel': 1,
                    'fonte': 'default',
                    'erro': str(e),
                    'razao': 'Erro ao calcular meteorologia',
                }
                logger.error(f"Erro ao calcular meteorologia: {e}")
        else:
            # Nível fornecido manualmente
            detalhes_meteorologia = {
                'nivel': nivel_meteo,
                'fonte': 'manual',
                'observacao': 'Entrada manual pelo operador',
            }

        # Validar níveis de entrada (1-5 padrão COR Rio)
        nivel_meteo = max(1, min(5, nivel_meteo)) if nivel_meteo and nivel_meteo > 0 else 1
        nivel_mob = max(1, min(5, nivel_mob)) if nivel_mob > 0 else 1
        nivel_eventos = max(1, min(5, nivel_eventos)) if nivel_eventos > 0 else 1

        # Aplicar pesos
        peso_total = self.matriz.peso_total

        nivel_ponderado = (
            nivel_meteo * float(self.matriz.peso_meteorologia) +
            nivel_incidentes * float(self.matriz.peso_incidentes) +
            nivel_mob * float(self.matriz.peso_mobilidade) +
            nivel_eventos * float(self.matriz.peso_eventos)
        ) / peso_total

        # Arredondar para nível inteiro (1-5 padrão COR Rio)
        nivel_cidade = round(nivel_ponderado)
        nivel_cidade = max(1, min(5, nivel_cidade))  # Garantir 1-5

        # Calcular proximidade do próximo nível
        if nivel_cidade < 5:
            proximidade = nivel_ponderado - int(nivel_ponderado)
        else:
            proximidade = 0  # Já no nível máximo (Crise)

        # Gerar justificativa detalhada
        justificativa_parts = [
            "═══════════════════════════════════════════",
            "         CÁLCULO DO ESTÁGIO OPERACIONAL",
            "═══════════════════════════════════════════",
            "",
            "▶ GRUPO 1 - METEOROLOGIA",
            f"  Nível: {nivel_meteo} × Peso: {self.matriz.peso_meteorologia} = {nivel_meteo * float(self.matriz.peso_meteorologia):.2f}",
            "",
            "▶ GRUPO 2 - INCIDENTES/OCORRÊNCIAS",
            f"  Nível: {nivel_incidentes} × Peso: {self.matriz.peso_incidentes} = {nivel_incidentes * float(self.matriz.peso_incidentes):.2f}",
            f"  Detalhes: {detalhes_incidentes['razao']}",
            f"  (Baixas: {detalhes_incidentes['baixas']} | Médias: {detalhes_incidentes['medias']} | Altas: {detalhes_incidentes['altas']} | Críticas: {detalhes_incidentes['criticas']})",
            "",
            "▶ GRUPO 3 - MOBILIDADE",
            f"  Nível: {nivel_mob} × Peso: {self.matriz.peso_mobilidade} = {nivel_mob * float(self.matriz.peso_mobilidade):.2f}",
            "",
            "▶ GRUPO 4 - EVENTOS",
            f"  Nível: {nivel_eventos} × Peso: {self.matriz.peso_eventos} = {nivel_eventos * float(self.matriz.peso_eventos):.2f}",
            "",
            "═══════════════════════════════════════════",
            f"  SOMA PONDERADA: {nivel_ponderado:.3f}",
            f"  PESO TOTAL: {peso_total}",
            "",
            f"  ★ NÍVEL DA CIDADE: {nivel_cidade} ({EstagioOperacional.NOMENCLATURA_NIVEIS[nivel_cidade].upper()})",
            f"  ★ PROXIMIDADE PRÓXIMO NÍVEL: {proximidade:.1%}",
            "═══════════════════════════════════════════",
        ]

        justificativa = '\n'.join(justificativa_parts)

        # Buscar ações recomendadas aplicáveis
        acoes_aplicaveis = AcaoRecomendada.objects.filter(
            matriz=self.matriz,
            ativa=True,
            nivel_minimo__lte=nivel_cidade,
            nivel_maximo__gte=nivel_cidade
        ).select_related('pop', 'categoria').prefetch_related('agencias').order_by('ordem')

        acoes_geradas = []
        for acao in acoes_aplicaveis:
            acoes_geradas.append({
                'id': str(acao.id),
                'titulo': acao.titulo,
                'descricao': acao.descricao,
                'prioridade': acao.prioridade_automatica,
                'prioridade_display': acao.get_prioridade_automatica_display(),
                'cor_prioridade': acao.cor_prioridade,
                'prazo_horas': acao.prazo_horas,
                'pop': {
                    'codigo': acao.pop.codigo,
                    'titulo': acao.pop.titulo,
                } if acao.pop else None,
                'categoria': {
                    'nome': acao.categoria.nome,
                    'icone': acao.categoria.icone,
                } if acao.categoria else None,
                'agencias': [
                    {'sigla': ag.sigla, 'nome': ag.nome}
                    for ag in acao.agencias.all()
                ],
            })

        # Criar registro de estágio
        estagio = EstagioOperacional.objects.create(
            matriz=self.matriz,
            nivel_meteorologia=nivel_meteo,
            nivel_incidentes=nivel_incidentes,
            nivel_mobilidade=nivel_mob,
            nivel_eventos=nivel_eventos,
            nivel_cidade=nivel_cidade,
            nivel_cidade_decimal=Decimal(str(round(nivel_ponderado, 3))),
            proximidade_proximo_nivel=Decimal(str(round(proximidade, 4))),
            dados_entrada={
                'nivel_meteo_input': nivel_meteo,
                'nivel_mob_input': nivel_mob,
                'nivel_eventos_input': nivel_eventos,
                'peso_total': peso_total,
                'matriz_versao': self.matriz.versao,
                'extras': dados_extras or {},
            },
            detalhes_meteorologia=detalhes_meteorologia,
            detalhes_incidentes=detalhes_incidentes,
            detalhes_mobilidade={
                'nivel': nivel_mob,
                'fonte': 'manual',
                'observacao': 'Entrada manual - integração com WAZE/CIMU pendente',
            },
            detalhes_eventos={
                'nivel': nivel_eventos,
                'fonte': 'manual',
                'observacao': 'Entrada manual - integração com agenda de eventos pendente',
            },
            justificativa=justificativa,
            acoes_geradas=acoes_geradas,
            solicitado_por=usuario,
        )

        logger.info(
            f"Estágio calculado: Nível {nivel_cidade} ({estagio.get_nomenclatura()}) "
            f"- ID: {estagio.id} - Por: {usuario}"
        )

        return estagio

    def obter_ultimo_estagio(self):
        """
        Retorna o último estágio calculado para a matriz atual

        Returns:
            EstagioOperacional ou None
        """
        from ..models import EstagioOperacional

        return EstagioOperacional.objects.filter(
            matriz=self.matriz
        ).order_by('-calculado_em').first()

    def obter_historico(self, horas: int = 24, limit: int = 100):
        """
        Retorna histórico de estágios calculados

        Args:
            horas: Horas retroativas (padrão 24)
            limit: Limite de registros (padrão 100)

        Returns:
            QuerySet de EstagioOperacional
        """
        from ..models import EstagioOperacional

        limite = timezone.now() - timedelta(hours=horas)

        return EstagioOperacional.objects.filter(
            matriz=self.matriz,
            calculado_em__gte=limite
        ).order_by('-calculado_em')[:limit]

    def obter_estatisticas(self, horas: int = 24) -> Dict:
        """
        Retorna estatísticas do período

        Args:
            horas: Horas retroativas

        Returns:
            Dict com estatísticas
        """
        from ..models import EstagioOperacional, OcorrenciaGerenciada
        from django.db.models import Avg, Max, Min

        limite = timezone.now() - timedelta(hours=horas)

        # Estatísticas de estágios
        estagios = EstagioOperacional.objects.filter(
            matriz=self.matriz,
            calculado_em__gte=limite
        )

        stats_estagios = estagios.aggregate(
            nivel_medio=Avg('nivel_cidade'),
            nivel_max=Max('nivel_cidade'),
            nivel_min=Min('nivel_cidade'),
            total_calculos=Count('id'),
        )

        # Estatísticas de ocorrências
        ocorrencias = OcorrenciaGerenciada.objects.filter(
            data_abertura__gte=limite
        )

        stats_ocorrencias = ocorrencias.aggregate(
            total=Count('id'),
            abertas=Count('id', filter=Q(status='aberta')),
            em_andamento=Count('id', filter=Q(status='em_andamento')),
            resolvidas=Count('id', filter=Q(status='resolvida')),
            fechadas=Count('id', filter=Q(status='fechada')),
            baixas=Count('id', filter=Q(prioridade='baixa')),
            medias=Count('id', filter=Q(prioridade='media')),
            altas=Count('id', filter=Q(prioridade='alta')),
            criticas=Count('id', filter=Q(prioridade='critica')),
        )

        return {
            'periodo_horas': horas,
            'estagios': stats_estagios,
            'ocorrencias': stats_ocorrencias,
        }
