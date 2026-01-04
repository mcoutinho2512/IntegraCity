"""
Views da Matriz Decisória
========================

Dashboard e APIs para o Motor de Decisão IntegraCity.
"""

import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta
import logging

from .models import (
    MatrizDecisoria,
    EstagioOperacional,
    AcaoRecomendada,
    OcorrenciaGerenciada
)
from .services.motor_decisao import MotorDecisao

logger = logging.getLogger(__name__)


@login_required
def matriz_dashboard(request):
    """
    Dashboard principal da Matriz Decisória.
    Exibe estágio atual, histórico e ações recomendadas.
    """
    context = {
        'erro': None,
        'matriz': None,
        'estagio': None,
        'historico': [],
        'grafico_data': [],
        'stats_ocorrencias': {},
        'acoes': [],
        'dados_chuva': {},
        'dados_mobilidade': {},
        'dados_meteorologia': {},
    }

    try:
        motor = MotorDecisao()
        matriz = motor.matriz
        context['matriz'] = matriz

        # Calcular estágio atual
        estagio_atual = motor.calcular_nivel_cidade(usuario=request.user)
        context['estagio'] = estagio_atual

        # Extrair detalhes do estágio para exibição
        context['dados_meteorologia'] = estagio_atual.detalhes_meteorologia or {}
        context['dados_mobilidade'] = estagio_atual.detalhes_mobilidade or {}

        # Histórico últimas 24h
        limite = timezone.now() - timedelta(hours=24)
        historico = EstagioOperacional.objects.filter(
            matriz=matriz,
            calculado_em__gte=limite
        ).order_by('calculado_em')

        context['historico'] = historico

        # Preparar dados para gráfico
        grafico_data = []
        for est in historico:
            grafico_data.append({
                'timestamp': est.calculado_em.strftime('%H:%M'),
                'timestamp_full': est.calculado_em.isoformat(),
                'nivel': est.nivel_cidade,
                'nivel_decimal': float(est.nivel_cidade_decimal),
                'nomenclatura': est.get_nomenclatura(),
                'cor': est.get_cor(),
            })
        context['grafico_data'] = json.dumps(grafico_data)

        # Estatísticas de ocorrências ATIVAS (todas abertas, independente da data)
        stats_ocorrencias = OcorrenciaGerenciada.objects.filter(
            status__in=['aberta', 'em_andamento', 'aguardando']
        ).aggregate(
            total=Count('id'),
            baixas=Count('id', filter=Q(prioridade='baixa')),
            medias=Count('id', filter=Q(prioridade='media')),
            altas=Count('id', filter=Q(prioridade='alta')),
            criticas=Count('id', filter=Q(prioridade='critica')),
        )
        context['stats_ocorrencias'] = stats_ocorrencias

        # Ações recomendadas para o nível atual
        context['acoes'] = estagio_atual.acoes_geradas

        # Buscar dados de chuva em tempo real (pluviômetros)
        try:
            import requests
            pluvio_response = requests.get(
                'https://websempre.rio.rj.gov.br/json/dados_pluviometricos',
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            if pluvio_response.ok:
                geojson = pluvio_response.json()
                features = geojson.get('features', [])
                total_pluvio = len(features)
                com_chuva = 0
                chuva_fraca = 0
                chuva_moderada = 0
                chuva_forte = 0
                max_chuva = 0
                estacao_max = ''

                for f in features:
                    props = f.get('properties', {})
                    data = props.get('data', {})
                    h01_str = data.get('h01', '0')
                    try:
                        h01 = float(str(h01_str).replace(',', '.'))
                    except:
                        h01 = 0

                    if h01 > 0:
                        com_chuva += 1
                        if h01 > max_chuva:
                            max_chuva = h01
                            estacao_max = props.get('station', {}).get('name', '')

                    if 0 < h01 <= 5:
                        chuva_fraca += 1
                    elif 5 < h01 <= 25:
                        chuva_moderada += 1
                    elif h01 > 25:
                        chuva_forte += 1

                context['dados_chuva'] = {
                    'total': total_pluvio,
                    'com_chuva': com_chuva,
                    'fraca': chuva_fraca,
                    'moderada': chuva_moderada,
                    'forte': chuva_forte,
                    'max_chuva': round(max_chuva, 1),
                    'estacao_max': estacao_max,
                }
        except Exception as e:
            logger.warning(f"Erro ao buscar pluviômetros: {e}")
            context['dados_chuva'] = {'erro': str(e)}

    except ValueError as e:
        context['erro'] = str(e)
        logger.warning(f"Erro ao carregar dashboard matriz: {e}")

    return render(request, 'matriz/dashboard.html', context)


@login_required
def matriz_historico(request):
    """
    Histórico de cálculos de estágio com filtros.
    """
    # Filtros
    dias = int(request.GET.get('dias', 7))
    nivel_filter = request.GET.get('nivel', '')

    limite = timezone.now() - timedelta(days=dias)

    estagios = EstagioOperacional.objects.filter(
        calculado_em__gte=limite
    ).select_related('matriz', 'solicitado_por')

    if nivel_filter:
        estagios = estagios.filter(nivel_cidade=int(nivel_filter))

    estagios = estagios.order_by('-calculado_em')[:100]

    # Estatísticas do período
    stats = EstagioOperacional.objects.filter(
        calculado_em__gte=limite
    ).aggregate(
        total=Count('id'),
        nivel_medio=Avg('nivel_cidade'),
        nivel_max=Max('nivel_cidade'),
        nivel_min=Min('nivel_cidade'),
    )

    context = {
        'estagios': estagios,
        'dias': dias,
        'nivel_filter': nivel_filter,
        'stats': stats,
        'nomenclaturas': EstagioOperacional.NOMENCLATURA_NIVEIS,
    }

    return render(request, 'matriz/historico.html', context)


@login_required
def matriz_detalhe_estagio(request, estagio_id):
    """
    Detalhes completos de um cálculo específico.
    """
    estagio = get_object_or_404(
        EstagioOperacional.objects.select_related('matriz', 'solicitado_por'),
        id=estagio_id
    )

    context = {
        'estagio': estagio,
    }

    return render(request, 'matriz/detalhe_estagio.html', context)


@login_required
@require_http_methods(["POST"])
def api_calcular_estagio(request):
    """
    API para calcular estágio atual.
    Aceita parâmetros opcionais para os grupos 1, 3 e 4.
    """
    try:
        # Parsear JSON do body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST

        # Parâmetros opcionais
        nivel_meteo = int(data.get('nivel_meteo', 0))
        nivel_mob = int(data.get('nivel_mob', 0))
        nivel_eventos = int(data.get('nivel_eventos', 0))

        # Validar range
        nivel_meteo = max(0, min(6, nivel_meteo))
        nivel_mob = max(0, min(6, nivel_mob))
        nivel_eventos = max(0, min(6, nivel_eventos))

        motor = MotorDecisao()
        estagio = motor.calcular_nivel_cidade(
            nivel_meteo=nivel_meteo,
            nivel_mob=nivel_mob,
            nivel_eventos=nivel_eventos,
            usuario=request.user
        )

        return JsonResponse({
            'success': True,
            'estagio_id': str(estagio.id),
            'nivel_cidade': estagio.nivel_cidade,
            'nomenclatura': estagio.get_nomenclatura(),
            'cor': estagio.get_cor(),
            'nivel_decimal': float(estagio.nivel_cidade_decimal),
            'proximidade_proximo': float(estagio.proximidade_proximo_nivel),
            'percentual_proximo': estagio.percentual_proximo_nivel,
            'niveis': {
                'meteorologia': estagio.nivel_meteorologia,
                'incidentes': estagio.nivel_incidentes,
                'mobilidade': estagio.nivel_mobilidade,
                'eventos': estagio.nivel_eventos,
            },
            'detalhes_incidentes': estagio.detalhes_incidentes,
            'detalhes_meteorologia': estagio.detalhes_meteorologia or {},
            'detalhes_mobilidade': estagio.detalhes_mobilidade or {},
            'acoes': estagio.acoes_geradas,
            'calculado_em': estagio.calculado_em.isoformat(),
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.exception("Erro ao calcular estágio")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno ao calcular estágio'
        }, status=500)


@login_required
def api_ultimo_estagio(request):
    """
    API para obter último estágio calculado.
    """
    try:
        motor = MotorDecisao()
        estagio = motor.obter_ultimo_estagio()

        if not estagio:
            return JsonResponse({
                'success': False,
                'error': 'Nenhum estágio calculado ainda'
            }, status=404)

        return JsonResponse({
            'success': True,
            'estagio_id': str(estagio.id),
            'nivel_cidade': estagio.nivel_cidade,
            'nomenclatura': estagio.get_nomenclatura(),
            'cor': estagio.get_cor(),
            'nivel_decimal': float(estagio.nivel_cidade_decimal),
            'percentual_proximo': estagio.percentual_proximo_nivel,
            'calculado_em': estagio.calculado_em.isoformat(),
            'tempo_desde': _tempo_desde(estagio.calculado_em),
            'niveis': {
                'meteorologia': estagio.nivel_meteorologia,
                'incidentes': estagio.nivel_incidentes,
                'mobilidade': estagio.nivel_mobilidade,
                'eventos': estagio.nivel_eventos,
            },
            'detalhes_incidentes': estagio.detalhes_incidentes,
            'detalhes_meteorologia': estagio.detalhes_meteorologia or {},
            'detalhes_mobilidade': estagio.detalhes_mobilidade or {},
            'acoes': estagio.acoes_geradas or [],
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.exception("Erro ao obter último estágio")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno'
        }, status=500)


@login_required
def api_historico_grafico(request):
    """
    API para dados do gráfico de histórico.
    """
    try:
        horas = int(request.GET.get('horas', 24))
        horas = max(1, min(168, horas))  # 1h a 7 dias

        motor = MotorDecisao()
        historico = motor.obter_historico(horas=horas, limit=200)

        dados = []
        for est in historico:
            dados.append({
                'timestamp': est.calculado_em.isoformat(),
                'hora': est.calculado_em.strftime('%H:%M'),
                'data': est.calculado_em.strftime('%d/%m'),
                'nivel': est.nivel_cidade,
                'nivel_decimal': float(est.nivel_cidade_decimal),
                'nomenclatura': est.get_nomenclatura(),
                'cor': est.get_cor(),
            })

        return JsonResponse({
            'success': True,
            'horas': horas,
            'total': len(dados),
            'dados': list(reversed(dados)),  # Ordenar cronologicamente
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.exception("Erro ao obter histórico")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno'
        }, status=500)


@login_required
def api_estatisticas(request):
    """
    API para estatísticas gerais.
    """
    try:
        horas = int(request.GET.get('horas', 24))
        horas = max(1, min(168, horas))

        motor = MotorDecisao()
        stats = motor.obter_estatisticas(horas=horas)

        return JsonResponse({
            'success': True,
            **stats
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.exception("Erro ao obter estatísticas")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno'
        }, status=500)


def _tempo_desde(dt):
    """Retorna tempo decorrido em formato legível."""
    delta = timezone.now() - dt
    segundos = delta.total_seconds()

    if segundos < 60:
        return f"{int(segundos)} segundo(s)"
    elif segundos < 3600:
        return f"{int(segundos // 60)} minuto(s)"
    elif segundos < 86400:
        return f"{int(segundos // 3600)} hora(s)"
    else:
        return f"{int(segundos // 86400)} dia(s)"
