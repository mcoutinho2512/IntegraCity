"""
Views de Meteorologia
====================

Dashboard e APIs para visualização dos dados meteorológicos do INMET.
Integrado ao Grupo 1 (Meteorologia) do Motor de Decisão.
"""

import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from .models import Cliente, EstacaoMeteorologica, DadosMeteorologicos


@login_required
def meteorologia_dashboard(request):
    """
    Dashboard principal de dados meteorológicos

    Mostra:
    - Nível meteorológico calculado
    - Dados de cada estação INMET
    - Gráficos de evolução
    - Botão para forçar coleta
    """

    # Buscar cliente ativo (primeiro)
    cliente = Cliente.objects.filter(ativo=True).first()

    if not cliente:
        return render(request, 'meteorologia/dashboard.html', {
            'erro': 'Nenhum cliente configurado. Execute: python manage.py configurar_cliente --help'
        })

    # Estações do cliente
    estacoes = EstacaoMeteorologica.objects.filter(
        cliente=cliente,
        ativa=True
    ).order_by('distancia_km')

    # Dados mais recentes de cada estação
    estacoes_com_dados = []
    for estacao in estacoes:
        ultimo_dado = estacao.get_ultimo_dado()
        estacoes_com_dados.append({
            'estacao': estacao,
            'ultimo_dado': ultimo_dado,
            'idade_minutos': ultimo_dado.idade_minutos if ultimo_dado else None,
        })

    # Calcular nível meteorológico
    nivel = 1
    detalhes = {}
    try:
        from .services.integrador_inmet import IntegradorINMET
        integrador = IntegradorINMET(cliente)
        nivel, detalhes = integrador.calcular_nivel_meteorologia()
    except Exception as e:
        detalhes = {'erro': str(e)}

    # Gráfico de evolução (últimas 24h)
    grafico_data = []
    estacao_principal = cliente.get_estacao_principal()
    if estacao_principal:
        limite = timezone.now() - timedelta(hours=24)
        dados_historico = DadosMeteorologicos.objects.filter(
            estacao=estacao_principal,
            data_hora__gte=limite
        ).order_by('data_hora')

        for dado in dados_historico:
            grafico_data.append({
                'timestamp': dado.data_hora.strftime('%H:%M'),
                'temperatura': float(dado.temperatura) if dado.temperatura else None,
                'umidade': float(dado.umidade) if dado.umidade else None,
                'chuva': float(dado.precipitacao_horaria) if dado.precipitacao_horaria else 0,
                'vento': float(dado.vento_velocidade) if dado.vento_velocidade else 0,
            })

    # Cores e nomenclatura por nível
    CORES_NIVEIS = {
        1: '#00ff88',
        2: '#00D4FF',
        3: '#FFB800',
        4: '#FF6B00',
        5: '#FF0055',
    }

    NOMENCLATURA_NIVEIS = {
        1: 'Normal',
        2: 'Mobilização',
        3: 'Atenção',
        4: 'Alerta',
        5: 'Crise',
    }

    context = {
        'cliente': cliente,
        'estacoes': estacoes_com_dados,
        'nivel': nivel,
        'nivel_cor': CORES_NIVEIS.get(nivel, '#00ff88'),
        'nivel_nome': NOMENCLATURA_NIVEIS.get(nivel, 'Normal'),
        'detalhes': detalhes,
        'grafico_data': json.dumps(grafico_data),
        'agora': timezone.now(),
    }

    return render(request, 'meteorologia/dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def api_coletar_agora(request):
    """
    API para forçar coleta imediata de dados meteorológicos

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

        from .services.integrador_inmet import IntegradorINMET
        integrador = IntegradorINMET(cliente)
        sucesso, total = integrador.coletar_todas_estacoes()

        # Calcular nível após coleta
        nivel, detalhes = integrador.calcular_nivel_meteorologia()

        return JsonResponse({
            'success': True,
            'coletados': sucesso,
            'total': total,
            'nivel': nivel,
            'detalhes': detalhes,
            'message': f'Dados coletados de {sucesso}/{total} estações'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_dados_estacao(request, codigo_inmet):
    """
    API para obter dados de uma estação específica

    Args:
        codigo_inmet: Código INMET da estação

    Retorna:
        JSON com dados da estação
    """

    try:
        estacao = EstacaoMeteorologica.objects.get(codigo_inmet=codigo_inmet)

        # Último dado
        ultimo = estacao.get_ultimo_dado()

        # Histórico (últimas 24h)
        limite = timezone.now() - timedelta(hours=24)
        historico = DadosMeteorologicos.objects.filter(
            estacao=estacao,
            data_hora__gte=limite
        ).order_by('-data_hora')[:48]

        dados_historico = []
        for d in historico:
            dados_historico.append({
                'data_hora': d.data_hora.isoformat(),
                'temperatura': float(d.temperatura) if d.temperatura else None,
                'umidade': float(d.umidade) if d.umidade else None,
                'pressao': float(d.pressao) if d.pressao else None,
                'chuva': float(d.precipitacao_horaria) if d.precipitacao_horaria else 0,
                'vento': float(d.vento_velocidade) if d.vento_velocidade else 0,
                'vento_rajada': float(d.vento_rajada) if d.vento_rajada else None,
                'vento_direcao': d.vento_direcao_cardeal,
            })

        return JsonResponse({
            'success': True,
            'estacao': {
                'nome': estacao.nome,
                'codigo': estacao.codigo_inmet,
                'latitude': float(estacao.latitude),
                'longitude': float(estacao.longitude),
                'altitude': float(estacao.altitude),
                'distancia_km': float(estacao.distancia_km),
                'principal': estacao.principal,
            },
            'ultimo_dado': {
                'data_hora': ultimo.data_hora.isoformat() if ultimo else None,
                'idade_minutos': ultimo.idade_minutos if ultimo else None,
                'temperatura': float(ultimo.temperatura) if ultimo and ultimo.temperatura else None,
                'umidade': float(ultimo.umidade) if ultimo and ultimo.umidade else None,
                'pressao': float(ultimo.pressao) if ultimo and ultimo.pressao else None,
                'chuva': float(ultimo.precipitacao_horaria) if ultimo and ultimo.precipitacao_horaria else 0,
                'vento': float(ultimo.vento_velocidade) if ultimo and ultimo.vento_velocidade else 0,
                'vento_rajada': float(ultimo.vento_rajada) if ultimo and ultimo.vento_rajada else None,
                'vento_direcao': ultimo.vento_direcao_cardeal if ultimo else None,
            } if ultimo else None,
            'historico': dados_historico,
        })

    except EstacaoMeteorologica.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Estação {codigo_inmet} não encontrada'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_nivel_meteorologia(request):
    """
    API para obter nível meteorológico atual

    Retorna:
        JSON com nível e detalhes
    """

    try:
        cliente = Cliente.objects.filter(ativo=True).first()

        if not cliente:
            return JsonResponse({
                'success': False,
                'nivel': 1,
                'error': 'Nenhum cliente configurado'
            })

        from .services.integrador_inmet import IntegradorINMET
        integrador = IntegradorINMET(cliente)
        nivel, detalhes = integrador.calcular_nivel_meteorologia()

        NOMENCLATURA = {
            1: 'Normal',
            2: 'Mobilização',
            3: 'Atenção',
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
def api_nivel_calor(request):
    """
    API para obter nível de calor atual (NC0-NC4)

    Calcula o Índice de Calor (Heat Index) baseado em temperatura e umidade,
    seguindo o protocolo COR Rio para ondas de calor.

    Níveis:
        NC0: Normal (IC < 36°C)
        NC1: Atenção (IC 36-40°C por 4h+)
        NC2: Alerta (IC 36-40°C por 6h+)
        NC3: Mobilização (IC 40-44°C por 2h+)
        NC4: Crise (IC > 44°C por 2h+)

    Retorna:
        JSON com nível de calor e detalhes do cálculo
    """

    try:
        cliente = Cliente.objects.filter(ativo=True).first()

        if not cliente:
            return JsonResponse({
                'success': False,
                'nivel': 0,
                'error': 'Nenhum cliente configurado'
            }, status=400)

        from .services.integrador_inmet import IntegradorINMET
        integrador = IntegradorINMET(cliente)
        nivel, detalhes = integrador.calcular_nivel_calor()

        return JsonResponse({
            'success': True,
            'nivel': nivel,
            'nomenclatura': f'NC{nivel}',
            'nome': detalhes.get('nomenclatura', 'Normal'),
            'cor': detalhes.get('cor', '#00ff88'),
            'ic_max': detalhes.get('ic_max'),
            'ic_medio': detalhes.get('ic_medio'),
            'temperatura_max': detalhes.get('temp_max'),
            'umidade_media': detalhes.get('umidade_media'),
            'horas_analisadas': detalhes.get('horas_analisadas'),
            'razao': detalhes.get('razao'),
            'detalhes': detalhes,
            'cliente': cliente.nome,
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'nivel': 0,
            'error': str(e)
        }, status=500)
