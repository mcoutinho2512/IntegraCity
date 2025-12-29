"""
Views de Mobilidade
====================

Dashboard e APIs para visualizacao dos dados de mobilidade (Waze).
Integrado ao Grupo 3 (Mobilidade) do Motor de Decisao.
"""

import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from .models import Cliente, DadosMobilidade


@login_required
def mobilidade_dashboard(request):
    """
    Dashboard principal de dados de mobilidade (Waze)

    Mostra:
    - Nivel de mobilidade calculado (E1-E5)
    - Estatisticas de congestionamentos
    - Alertas e acidentes
    - Vias interditadas
    - Grafico de evolucao
    - Botao para forcar coleta
    """

    # Buscar cliente ativo (primeiro)
    cliente = Cliente.objects.filter(ativo=True).first()

    if not cliente:
        return render(request, 'mobilidade/dashboard.html', {
            'erro': 'Nenhum cliente configurado. Execute: python manage.py configurar_cliente --help'
        })

    # Verificar se tem feed_id configurado
    feed_id = cliente.config_apis.get('waze_feed_id') if cliente.config_apis else None
    has_feed = bool(feed_id)

    # Dados mais recentes
    ultimo_dado = DadosMobilidade.objects.filter(
        cliente=cliente
    ).order_by('-data_hora').first()

    # Calcular nivel de mobilidade
    nivel = 1
    detalhes = {}
    try:
        from .services.integrador_waze import IntegradorWaze
        integrador = IntegradorWaze(cliente)
        nivel, detalhes = integrador.calcular_nivel_mobilidade()
    except Exception as e:
        detalhes = {'erro': str(e)}

    # Grafico de evolucao (ultimas 24h)
    grafico_data = []
    limite = timezone.now() - timedelta(hours=24)
    dados_historico = DadosMobilidade.objects.filter(
        cliente=cliente,
        data_hora__gte=limite
    ).order_by('data_hora')

    for dado in dados_historico:
        grafico_data.append({
            'timestamp': dado.data_hora.strftime('%H:%M'),
            'jams_severos': dado.jams_severos,
            'jams_moderados': dado.jams_moderados,
            'acidentes': dado.acidentes_maiores + dado.acidentes_menores,
            'total_jams': dado.total_jams,
        })

    # Cores e nomenclatura por nivel
    CORES_NIVEIS = {
        1: '#00ff88',
        2: '#00D4FF',
        3: '#FFB800',
        4: '#FF6B00',
        5: '#FF0055',
    }

    NOMENCLATURA_NIVEIS = {
        1: 'Normal',
        2: 'Mobilizacao',
        3: 'Atencao',
        4: 'Alerta',
        5: 'Crise',
    }

    context = {
        'cliente': cliente,
        'has_feed': has_feed,
        'feed_id': feed_id,
        'ultimo_dado': ultimo_dado,
        'nivel': nivel,
        'nivel_cor': CORES_NIVEIS.get(nivel, '#00ff88'),
        'nivel_nome': NOMENCLATURA_NIVEIS.get(nivel, 'Normal'),
        'detalhes': detalhes,
        'grafico_data': json.dumps(grafico_data),
        'agora': timezone.now(),
    }

    return render(request, 'mobilidade/dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def api_coletar_mobilidade_agora(request):
    """
    API para forcar coleta imediata de dados de mobilidade

    Retorna:
        JSON com resultado da coleta
    """

    try:
        cliente = Cliente.objects.filter(ativo=True).first()

        if not cliente:
            return JsonResponse({
                'success': False,
                'error': 'Nenhum cliente configurado'
            }, status=400)

        from .services.integrador_waze import IntegradorWaze
        integrador = IntegradorWaze(cliente)
        dados = integrador.coletar_dados()

        if dados:
            # Calcular nivel apos coleta
            nivel, detalhes = integrador.calcular_nivel_mobilidade()

            return JsonResponse({
                'success': True,
                'total_jams': dados.total_jams,
                'jams_severos': dados.jams_severos,
                'total_alerts': dados.total_alerts,
                'acidentes': dados.acidentes_maiores + dados.acidentes_menores,
                'nivel': nivel,
                'nivel_nome': detalhes.get('nomenclatura', 'Normal'),
                'message': f'Dados coletados: {dados.total_jams} jams ({dados.jams_severos} severos)'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Falha na coleta. Verifique configuracao do feed_id.'
            }, status=500)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_nivel_mobilidade(request):
    """
    API para obter nivel de mobilidade atual

    Retorna:
        JSON com nivel e detalhes
    """

    try:
        cliente = Cliente.objects.filter(ativo=True).first()

        if not cliente:
            return JsonResponse({
                'success': False,
                'nivel': 1,
                'error': 'Nenhum cliente configurado'
            })

        from .services.integrador_waze import IntegradorWaze
        integrador = IntegradorWaze(cliente)
        nivel, detalhes = integrador.calcular_nivel_mobilidade()

        NOMENCLATURA = {
            1: 'Normal',
            2: 'Mobilizacao',
            3: 'Atencao',
            4: 'Alerta',
            5: 'Crise',
        }

        CORES = {
            1: '#00ff88',
            2: '#00D4FF',
            3: '#FFB800',
            4: '#FF6B00',
            5: '#FF0055',
        }

        return JsonResponse({
            'success': True,
            'nivel': nivel,
            'nomenclatura': NOMENCLATURA.get(nivel, 'Normal'),
            'cor': CORES.get(nivel, '#00ff88'),
            'detalhes': detalhes,
            'cliente': cliente.nome,
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'nivel': 1,
            'error': str(e)
        }, status=500)


@login_required
def api_dados_mobilidade(request):
    """
    API para obter dados de mobilidade atual

    Retorna:
        JSON com dados completos
    """

    try:
        cliente = Cliente.objects.filter(ativo=True).first()

        if not cliente:
            return JsonResponse({
                'success': False,
                'error': 'Nenhum cliente configurado'
            }, status=400)

        # Ultimo dado coletado
        ultimo = DadosMobilidade.objects.filter(
            cliente=cliente
        ).order_by('-data_hora').first()

        if not ultimo:
            return JsonResponse({
                'success': False,
                'error': 'Nenhum dado de mobilidade coletado ainda'
            }, status=404)

        # Historico (ultimas 24h)
        limite = timezone.now() - timedelta(hours=24)
        historico = DadosMobilidade.objects.filter(
            cliente=cliente,
            data_hora__gte=limite
        ).order_by('-data_hora')[:48]

        dados_historico = []
        for d in historico:
            dados_historico.append({
                'data_hora': d.data_hora.isoformat(),
                'total_jams': d.total_jams,
                'jams_severos': d.jams_severos,
                'jams_moderados': d.jams_moderados,
                'total_alerts': d.total_alerts,
                'acidentes_maiores': d.acidentes_maiores,
                'acidentes_menores': d.acidentes_menores,
                'vias_interditadas': d.vias_interditadas,
                'velocidade_media': float(d.velocidade_media_kmh) if d.velocidade_media_kmh else None,
            })

        # Calcular nivel
        from .services.integrador_waze import IntegradorWaze
        integrador = IntegradorWaze(cliente)
        nivel, detalhes = integrador.calcular_nivel_mobilidade()

        return JsonResponse({
            'success': True,
            'cliente': cliente.nome,
            'nivel': nivel,
            'ultimo_dado': {
                'data_hora': ultimo.data_hora.isoformat(),
                'idade_minutos': ultimo.idade_minutos,
                'total_jams': ultimo.total_jams,
                'jams_severos': ultimo.jams_severos,
                'jams_moderados': ultimo.jams_moderados,
                'jams_leves': ultimo.jams_leves,
                'total_alerts': ultimo.total_alerts,
                'acidentes_maiores': ultimo.acidentes_maiores,
                'acidentes_menores': ultimo.acidentes_menores,
                'perigos': ultimo.perigos,
                'total_irregularidades': ultimo.total_irregularidades,
                'vias_interditadas': ultimo.vias_interditadas,
                'obras': ultimo.obras,
                'velocidade_media_kmh': float(ultimo.velocidade_media_kmh) if ultimo.velocidade_media_kmh else None,
                'atraso_medio_minutos': round(ultimo.atraso_medio_segundos / 60, 1) if ultimo.atraso_medio_segundos else None,
                'extensao_total_km': ultimo.extensao_total_km,
            },
            'detalhes': detalhes,
            'historico': dados_historico,
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_jams_mapa(request):
    """
    API para obter congestionamentos para mapa

    Retorna:
        JSON com lista de jams com coordenadas
    """

    try:
        cliente = Cliente.objects.filter(ativo=True).first()

        if not cliente:
            return JsonResponse({
                'success': False,
                'error': 'Nenhum cliente configurado'
            }, status=400)

        from .services.integrador_waze import IntegradorWaze
        integrador = IntegradorWaze(cliente)
        jams = integrador.obter_jams_para_mapa()

        return JsonResponse({
            'success': True,
            'total': len(jams),
            'jams': jams,
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_alerts_mapa(request):
    """
    API para obter alertas para mapa

    Retorna:
        JSON com lista de alerts com coordenadas
    """

    try:
        cliente = Cliente.objects.filter(ativo=True).first()

        if not cliente:
            return JsonResponse({
                'success': False,
                'error': 'Nenhum cliente configurado'
            }, status=400)

        from .services.integrador_waze import IntegradorWaze
        integrador = IntegradorWaze(cliente)
        alerts = integrador.obter_alerts_para_mapa()

        return JsonResponse({
            'success': True,
            'total': len(alerts),
            'alerts': alerts,
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_resumo_mobilidade(request):
    """
    API para obter resumo de mobilidade para dashboard principal

    Retorna:
        JSON com resumo compacto
    """

    try:
        cliente = Cliente.objects.filter(ativo=True).first()

        if not cliente:
            return JsonResponse({
                'success': False,
                'nivel': 1,
                'error': 'Nenhum cliente configurado'
            })

        from .services.integrador_waze import IntegradorWaze
        integrador = IntegradorWaze(cliente)
        resumo = integrador.obter_resumo_mobilidade()

        return JsonResponse({
            'success': resumo.get('disponivel', False),
            **resumo
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'nivel': 1,
            'error': str(e)
        }, status=500)


@login_required
def api_waze_completo(request):
    """
    API para obter todos os dados do Waze categorizados para o mapa

    Retorna:
        JSON com:
            - congestionamentos: Lista de jams (DYNAMIC)
            - interdicoes: Lista de vias interditadas (ROAD_CLOSED)
            - eventos: Lista de eventos especiais (STATIC)
            - rotas_transito: Rotas com transito alto
            - alertas: Acidentes, perigos, etc
            - estatisticas: Contagens por tipo
    """

    def _mapear_feed_partner(raw):
        congestionamentos = []
        alertas = []
        interdicoes = []

        jams = raw.get('jams', [])
        for jam in jams:
            line = jam.get('line', [])
            if not line:
                continue
            congestionamentos.append({
                'id': jam.get('uuid', ''),
                'category': 'congestionamento',
                'street': jam.get('street', 'Via nao identificada'),
                'toName': jam.get('endNode', ''),
                'level': jam.get('level', 0),
                'speed': round(jam.get('speedKMH', 0), 1),
                'length': jam.get('length', 0),
                'delay': jam.get('delay', 0),
                'coordinates': [(p.get('x'), p.get('y')) for p in line],
            })

        alerts_raw = raw.get('alerts', [])
        for alert in alerts_raw:
            location = alert.get('location', {})
            if not location:
                continue
            alertas.append({
                'id': alert.get('uuid', ''),
                'type': alert.get('type', ''),
                'subtype': alert.get('subtype', ''),
                'street': alert.get('street', 'Local nao identificado'),
                'city': alert.get('city', ''),
                'confidence': alert.get('confidence', 0),
                'reliability': alert.get('reliability', 0),
                'lat': location.get('y'),
                'lon': location.get('x'),
            })

            if alert.get('type') == 'ROAD_CLOSED' and location.get('y') and location.get('x'):
                lat = location.get('y')
                lon = location.get('x')
                delta = 0.0008
                interdicoes.append({
                    'id': alert.get('uuid', ''),
                    'street': alert.get('street', 'Via nao identificada'),
                    'reason': alert.get('subtype', 'ROAD_CLOSED'),
                    'length': 50,
                    'coordinates': [(lon - delta, lat - delta), (lon + delta, lat + delta)],
                })

        return {
            'congestionamentos': congestionamentos,
            'interdicoes': interdicoes,
            'eventos': [],
            'rotas_transito': [],
            'alertas': alertas,
            'estatisticas': {
                'total_congestionamentos': len(congestionamentos),
                'total_interdicoes': len(interdicoes),
                'total_eventos': 0,
                'total_rotas_transito': 0,
                'total_alertas': len(alertas),
            }
        }

    try:
        cliente = Cliente.objects.filter(ativo=True).first()

        if not cliente:
            return JsonResponse({
                'success': False,
                'error': 'Nenhum cliente configurado'
            }, status=400)

        from .services.integrador_waze import IntegradorWaze
        integrador = IntegradorWaze(cliente)
        dados = integrador.obter_dados_completos_mapa()

        stats = dados.get('estatisticas', {}) if isinstance(dados, dict) else {}
        sem_dados = not stats or sum([
            stats.get('total_congestionamentos', 0),
            stats.get('total_interdicoes', 0),
            stats.get('total_eventos', 0),
            stats.get('total_alertas', 0)
        ]) == 0

        if sem_dados:
            import requests
            partner_id = cliente.config_apis.get('waze_partner_id') if cliente.config_apis else None
            feed_id = cliente.config_apis.get('waze_feed_id') if cliente.config_apis else None

            if not partner_id or not feed_id:
                partner_id = '14420996249'
                feed_id = 'c5c19146-e0f9-44a7-9815-3862c8a6ed67'

            url = f"https://www.waze.com/row-partnerhub-api/partners/{partner_id}/waze-feeds/{feed_id}?format=1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            raw = response.json()
            dados = _mapear_feed_partner(raw)

        return JsonResponse({
            'success': True,
            **dados
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def api_vias_engarrafadas(request):
    """
    API para obter lista de vias engarrafadas
    
    Query params:
        nivel_minimo: Nível mínimo de congestionamento (0-4)
    
    Returns:
        JSON com lista de vias
    """
    
    try:
        cliente = Cliente.objects.filter(ativo=True).first()
        
        if not cliente:
            return JsonResponse({
                'success': False,
                'error': 'Nenhum cliente configurado'
            }, status=400)
        
        # Parâmetro de nível mínimo
        nivel_minimo = int(request.GET.get('nivel_minimo', 2))
        
        from .services.integrador_waze import IntegradorWaze
        integrador = IntegradorWaze(cliente)
        vias = integrador.obter_vias_engarrafadas(nivel_minimo=nivel_minimo)
        
        return JsonResponse({
            'success': True,
            'total': len(vias),
            'nivel_minimo': nivel_minimo,
            'vias': vias,
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_alertas_categorizados(request):
    """
    API para obter alertas separados por categoria
    
    Returns:
        JSON com acidentes, interdições, perigos, outros
    """
    
    try:
        cliente = Cliente.objects.filter(ativo=True).first()
        
        if not cliente:
            return JsonResponse({
                'success': False,
                'error': 'Nenhum cliente configurado'
            }, status=400)
        
        from .services.integrador_waze import IntegradorWaze
        integrador = IntegradorWaze(cliente)
        alertas = integrador.obter_alertas_categorizados()
        
        return JsonResponse({
            'success': True,
            **alertas
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def vias_engarrafadas_view(request):
    """
    Página com lista de vias engarrafadas
    """
    
    cliente = Cliente.objects.filter(ativo=True).first()
    
    if not cliente:
        return render(request, 'mobilidade/vias_engarrafadas.html', {
            'erro': 'Nenhum cliente configurado'
        })
    
    # Verificar se tem feed_id configurado
    feed_id = cliente.config_apis.get('waze_feed_id') if cliente.config_apis else None
    has_feed = bool(feed_id)
    
    # Obter vias engarrafadas
    vias = []
    try:
        from .services.integrador_waze import IntegradorWaze
        integrador = IntegradorWaze(cliente)
        vias = integrador.obter_vias_engarrafadas(nivel_minimo=2)
    except Exception as e:
        pass
    
    # Separar por nível
    vias_severas = [v for v in vias if v['nivel'] >= 4]  # Parado
    vias_intensas = [v for v in vias if v['nivel'] == 3]  # Intenso
    vias_moderadas = [v for v in vias if v['nivel'] == 2]  # Moderado
    
    context = {
        'cliente': cliente,
        'has_feed': has_feed,
        'feed_id': feed_id,
        'vias': vias,
        'vias_severas': vias_severas,
        'vias_intensas': vias_intensas,
        'vias_moderadas': vias_moderadas,
        'total_vias': len(vias),
        'agora': timezone.now(),
    }
    
    return render(request, 'mobilidade/vias_engarrafadas.html', context)


@login_required
def alertas_categorizados_view(request):
    """
    Página com alertas separados por categoria
    """
    
    cliente = Cliente.objects.filter(ativo=True).first()
    
    if not cliente:
        return render(request, 'mobilidade/alertas_categorizados.html', {
            'erro': 'Nenhum cliente configurado'
        })
    
    # Verificar se tem feed_id configurado
    feed_id = cliente.config_apis.get('waze_feed_id') if cliente.config_apis else None
    has_feed = bool(feed_id)
    
    # Obter alertas categorizados
    alertas = {
        'acidentes': [],
        'interdicoes': [],
        'perigos': [],
        'outros': [],
        'total': 0,
    }
    
    try:
        from .services.integrador_waze import IntegradorWaze
        integrador = IntegradorWaze(cliente)
        alertas = integrador.obter_alertas_categorizados()
    except Exception as e:
        pass
    
    context = {
        'cliente': cliente,
        'has_feed': has_feed,
        'feed_id': feed_id,
        'acidentes': alertas['acidentes'],
        'interdicoes': alertas['interdicoes'],
        'perigos': alertas['perigos'],
        'outros': alertas['outros'],
        'total_alertas': alertas['total'],
        'agora': timezone.now(),
    }
    
    return render(request, 'mobilidade/alertas_categorizados.html', context)