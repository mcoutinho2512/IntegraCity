import re
import random
import base64
import urllib3
from django.shortcuts import render
from functools import lru_cache
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required  
from django.utils import timezone
from datetime import datetime, timedelta
from datetime import datetime
import logging
import requests  #IMPORT ADICIONADO

# Configuração do Logger
logger = logging.getLogger(__name__)
from .models import (
    Sirene,
    DadosSirene,
    Estagio,
    ChuvaConsolidado,
    Evento,
    Ocorrencias,
    EstacaoPlv,
    DadosPlv,
    EstacaoMet,
    DadosMet,
    EscolasMunicipais,
    BensProtegidos,
    Calor
)

def teste_sem_login(request):
    """Teste sem login"""
    from django.http import HttpResponse
    return HttpResponse('<h1>FUNCIONOU! SEM LOGIN!</h1>')

# ============================================
# VIEWS DE PÁGINAS
# ============================================

@login_required(login_url='login')
@never_cache
def waze_dashboard_view(request):
    """Dashboard principal do mapa"""
    return render(request, 'mapa_novo/waze_dashboard.html')

# ============================================
# APIs - SIRENES
# ============================================

@never_cache
def sirene_api(request):
    """
    API de Sirenes - Retorna APENAS sirenes ATIVAS/ACIONADAS
    Filtro:
    - Fonte COR: status == "ativa"
    - Fonte Defesa Civil: tipo != "Desligada"
    """
    try:
        lista_estacoes = []
        sirenes = Sirene.objects.all()

        for sirene in sirenes:
            try:
                # Pegar último dado da sirene
                dados = DadosSirene.objects.filter(estacao_id=sirene.id).latest('id')

                status = dados.status if hasattr(dados, 'status') else "inativa"
                tipo = dados.tipo if hasattr(dados, 'tipo') else "Desligada"
                fonte = sirene.fonte if hasattr(sirene, 'fonte') else "COR"
                
                # ✅ FILTRO: Apenas sirenes ativas
                if fonte == "COR":
                    # Fonte COR: status deve ser "ativa"
                    if status.lower() != "ativa":
                        continue  # Pular esta sirene
                else:
                    # Fonte Defesa Civil: tipo deve ser diferente de "Desligada"
                    if tipo == "Desligada":
                        continue  # Pular esta sirene

                # Se passou pelo filtro, adicionar
                lista_estacoes.append({
                    "id": sirene.id,
                    "fonte": fonte,
                    "lat": float(sirene.lat) if sirene.lat else -22.9068,
                    "lng": float(sirene.lon) if sirene.lon else -43.1729,
                    "nome": sirene.nome,
                    "cidade": sirene.municipio if hasattr(sirene, 'municipio') else "Rio de Janeiro",
                    "status": status,
                    "tipo": tipo,
                    "prioridade": tipo
                })
                
            except DadosSirene.DoesNotExist:
                # Se não tem dados, considerar como inativa e pular
                continue

        # Ordenar por tipo (prioridade)
        lista_ordenada = sorted(lista_estacoes, key=lambda k: k.get('tipo', 'baixa'), reverse=True)
        
        ativas = len(lista_ordenada)
        logger.info(f"🚨 {ativas} sirenes ATIVAS no momento")

        return JsonResponse({
            'success': True,
            'count': ativas,
            'ativas': ativas,
            'data': lista_ordenada
        })

    except Exception as e:
        logger.error(f"❌ Erro na API de sirenes: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)


# ============================================
# APIs - ESTÁGIOS DE MOBILIDADE
# ============================================

@never_cache
def estagio_api(request):
    """
    API de Estágios de Mobilidade
    Retorna o estágio atual da cidade
    """
    try:
        av = Estagio.objects.latest('id')

        # Extrair número do texto "Nível X"
        estagio_texto = av.esta or 'Nível 1'
        match = re.search(r'(\d+)', estagio_texto)
        nivel = int(match.group(1)) if match else 1

        # Mapeamento de cores por nível
        cores_map = {
            1: '#228d46',  # Verde - Normalidade
            2: '#f5c520',  # Amarelo - Atenção
            3: '#ef8c3f',  # Laranja - Alerta
            4: '#d0262d',  # Vermelho - Alerta Máximo
            5: '#5f2f7e'   # Roxo - Crise
        }

        nomes_map = {
            1: 'Normalidade',
            2: 'Atenção',
            3: 'Alerta',
            4: 'Alerta Máximo',
            5: 'Crise'
        }

        return JsonResponse({
            'success': True,
            'estagio': estagio_texto,
            'estagio_id': nivel,
            'nivel': nivel,
            'cor': cores_map.get(nivel, '#228d46'),
            'nome': nomes_map.get(nivel, 'Normalidade'),
            'mensagem': av.men if hasattr(av, 'men') else '',
            'inicio': av.data_i.isoformat() if hasattr(av, 'data_i') and av.data_i else None,
            'data_atualizacao': datetime.now().isoformat()
        })

    except Estagio.DoesNotExist:
        return JsonResponse({
            'success': True,
            'estagio': 'Nível 1',
            'estagio_id': 1,
            'nivel': 1,
            'cor': '#228d46',
            'nome': 'Normalidade',
            'mensagem': 'Sistema operando normalmente',
            'inicio': None,
            'data_atualizacao': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def estagio_api_app(request):
    """API de estágio para app mobile (formato simplificado)"""
    try:
        av = Estagio.objects.latest('id')
        estagio = av.esta.upper()
        return HttpResponse(estagio)
    except:
        return HttpResponse("NORMALIDADE")


# ============================================
# APIs - CHUVA/METEOROLOGIA
# ============================================

@cache_page(60 * 5)  # Cache de 5 minutos
def chuva_api(request):
    """
    API de Dados de Chuva
    Retorna último consolidado de chuva
    """
    try:
        consolidado = ChuvaConsolidado.objects.latest('id')

        return JsonResponse({
            'success': True,
            'data': {
                'id': consolidado.id,
                'valor': str(consolidado) if consolidado else 'N/A',
                'data_atualizacao': datetime.now().isoformat()
            }
        })
    except ChuvaConsolidado.DoesNotExist:
        return JsonResponse({
            'success': True,
            'data': {
                'valor': 'Sem dados',
                'data_atualizacao': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================
# APIs - EVENTOS
# ============================================

@never_cache
def api_eventos(request):
    """API de eventos da cidade"""
    try:
        eventos = Evento.objects.all()[:50]  # Últimos 50 eventos

        data = []
        for evento in eventos:
            data.append({
                'id': evento.id,
                'nome': evento.nome if hasattr(evento, 'nome') else 'Evento',
                'tipo': evento.tipo if hasattr(evento, 'tipo') else 'geral',
                'lat': float(evento.lat) if hasattr(evento, 'lat') and evento.lat else -22.9068,
                'lng': float(evento.lon) if hasattr(evento, 'lon') and evento.lon else -43.1729,
                'data': evento.data.isoformat() if hasattr(evento, 'data') and evento.data else None,
                'prioridade': evento.prioridade if hasattr(evento, 'prioridade') else 'media',
                'local': evento.local if hasattr(evento, 'local') else ''
            })

        return JsonResponse({
            'success': True,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)


# ============================================
# APIs - OCORRÊNCIAS
# ============================================

@api_view(['GET'])
def api_ocorrencias_hoje(request):
    """
    API REST - Ocorrências de HOJE
    Usando o modelo Ocorrencias existente
    """
    try:
        # Data de hoje
        hoje = timezone.now().date()
        inicio_dia = timezone.make_aware(datetime.combine(hoje, datetime.min.time()))
        fim_dia = timezone.make_aware(datetime.combine(hoje, datetime.max.time()))
        
        # Buscar ocorrências ABERTAS (não concluídas)
        ocorrencias = Ocorrencias.objects.exclude(
        status='Concluído'
        ).order_by('-data') 
        
        total = ocorrencias.count()
        
        # Mapear prioridades para cores
        cores_prioridade = {
            'SECUNDÁRIO': '#10b981',  # Verde
            'BAIXO': '#10b981',        # Verde
            'MEDIO': '#f59e0b',        # Amarelo
            'ALTO': '#ef4444',         # Vermelho
            'CRITICO': '#991b1b',      # Vermelho escuro
        }
        
        # Mapear tipos para ícones
        icones_tipo = {
            'ACIDENTE': 'bi-car-front-fill',
            'ALAGAMENTO': 'bi-water',
            'DESLIZAMENTO': 'bi-exclamation-triangle-fill',
            'QUEDA DE ÁRVORE': 'bi-tree-fill',
            'INCÊNDIO': 'bi-fire',
            'VAZAMENTO': 'bi-droplet-fill',
            'BURACO': 'bi-sign-stop-fill',
        }
        
        # Formatar dados
        dados = []
        for occ in ocorrencias:
            # Determinar ícone baseado no tipo de incidente
            icone = 'bi-exclamation-circle-fill'  # padrão
            if occ.incidente:
                incidente_upper = occ.incidente.upper()
                for key, icon in icones_tipo.items():
                    if key in incidente_upper:
                        icone = icon
                        break
            
            dados.append({
                'id': occ.id,
                'id_c': occ.id_c or '',
                'tipo': occ.incidente or 'Outros',
                'descricao': occ.obs or 'Sem descrição',
                'endereco': occ.log or 'Endereço não informado',
                'bairro': occ.bairro or '',
                'lat': float(occ.lat) if occ.lat else None,
                'lng': float(occ.lon) if occ.lon else None,
                'prioridade': occ.prio or 'MEDIO',
                'cor_prioridade': cores_prioridade.get(occ.prio, '#6b7280'),
                'status': occ.status or 'Acionado',
                'icone': icone,
                'data_criacao': occ.data.isoformat() if occ.data else None,
                'esta_aberta': occ.status != 'Concluído' if occ.status else True,
            })
        
        # Estatísticas
        abertas = ocorrencias.exclude(status='Concluído').count()
        concluidas = ocorrencias.filter(status='Concluído').count()
        
        return Response({
            'success': True,
            'data': dados,
            'estatisticas': {
                'total': total,
                'abertas': abertas,
                'concluidas': concluidas,
            },
            'filtro': {
                'tipo': 'hoje',
                'data': hoje.isoformat(),
            },
            'timestamp': timezone.now().isoformat(),
        })
        
    except Exception as e:
        logger.error(f'❌ Erro ao buscar ocorrências: {str(e)}', exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'data': [],
        }, status=500)

@csrf_exempt
def api_ocorrencias(request):
    """
    API de ocorrências - APENAS DO DIA ATUAL
    """
    try:
        from django.utils import timezone  # ← Importar do Django
        
        # MOSTRAR TODAS AS ABERTAS
        ocorrencias = Ocorrencias.objects.exclude(
        status='Concluído'
        ).order_by('-data')  # Mais recentes primeiro   
        
        total = ocorrencias.count()
        
        data = []
        for ocorrencia in ocorrencias:
            data.append({
                'id': ocorrencia.id,
                'id_c': ocorrencia.id_c,
                'incidente': ocorrencia.incidente,
                'location': ocorrencia.location,
                'lat': float(ocorrencia.lat) if ocorrencia.lat else None,
                'lon': float(ocorrencia.lon) if ocorrencia.lon else None,
                'prio': ocorrencia.prio,
                'status': ocorrencia.status,
                'data': ocorrencia.data.isoformat() if ocorrencia.data else None,
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': total,
            'filtro': 'hoje',
            'data_filtro': hoje.isoformat()
        })
        
    except Exception as e:
        logger.error(f'Erro ao buscar ocorrências: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)

# ============================================
# APIs - OUTRAS (Placeholder para expansão futura)
# ============================================

def api_escolas(request):
    """API de escolas (placeholder)"""
    return JsonResponse({'success': True, 'count': 0, 'data': []})

def api_hospitais(request):
    """API de hospitais (placeholder)"""
    return JsonResponse({'success': True, 'count': 0, 'data': []})


def waze_dashboard_completo(request):
    """Dashboard completo com todas as estatísticas"""
    context = {
        'tamanho_4': 0,
        'pc': 0,
        'color_pc': '228d46',
        'hist': 0,
        'unz': [],
        'qt_unz': 0,
        'baixo_v': 0,
        'medio_v': 0,
        'alto_v': 0,
        'lista_estacoes_plv': [],
        'jams_linha': [],
        'escolas': [],
        'hospitais': [],
        'eventos': [],
        'ocorrencias': [],
        'sirenes': [],
        'abrigos': [],
        'alagamentos': [],
        'bens': [],
        'chuva': [],
        'lista_pontos': [],
        'sensores': []
    }

    return render(request, 'mapa_novo/waze_dashboard.html', context)

@login_required(login_url='login')
@never_cache
def cor_dashboard_view(request):
    """Dashboard High-Tech Command Center (PRINCIPAL)"""
    # Redireciona para a mesma logica do hightech
    return cor_dashboard_hightech_view(request)


@login_required(login_url='login')
@never_cache
def cor_dashboard_hightech_view(request):
    """Dashboard High-Tech Command Center"""
    from datetime import date, timedelta
    from django.db.models import Count

    # Estagio atual
    try:
        estagio_obj = Estagio.objects.latest('data_i')
        estagio_map = {
            'Normalidade': 1,
            'Mobilizacao': 2,
            'Atencao': 3,
            'Alerta': 4,
            'Crise': 5,
        }
        estagio = estagio_map.get(estagio_obj.esta, 1)
        estagio_label = estagio_obj.esta or 'Normalidade'
    except:
        estagio = 1
        estagio_label = 'Normalidade'

    # Ocorrencias abertas (sem data_f)
    try:
        ocorrencias = Ocorrencias.objects.filter(data_f__isnull=True).order_by('-data')[:100]
        ocorrencias_count = ocorrencias.count()
        ocorrencias_hoje = Ocorrencias.objects.filter(
            data__date=date.today(),
            data_f__isnull=True
        ).count()
    except:
        ocorrencias = []
        ocorrencias_count = 0
        ocorrencias_hoje = 0

    # Eventos de hoje
    try:
        eventos_count = Evento.objects.filter(data__gte=date.today()).count()
        eventos_semana = Evento.objects.filter(
            data__gte=date.today(),
            data__lte=date.today() + timedelta(days=7)
        ).count()
    except:
        eventos_count = 0
        eventos_semana = 0

    # Sirenes
    try:
        sirenes = Sirene.objects.all()
        sirenes_total = sirenes.count()
        sirenes_acionadas = 0  # Implementar logica real
        sirenes_operantes = sirenes_total
    except:
        sirenes = []
        sirenes_total = 0
        sirenes_acionadas = 0
        sirenes_operantes = 0

    # Indice de calor
    try:
        calor_obj = Calor.objects.latest('data')
        calor_index = calor_obj.nivel if hasattr(calor_obj, 'nivel') else 1
        calor_label = calor_obj.descricao if hasattr(calor_obj, 'descricao') else 'Normal'
    except:
        calor_index = 1
        calor_label = 'Normal'

    # Meteorologia
    try:
        meteo = DadosMet.objects.order_by('-data').first()
        if meteo:
            temperatura = round(meteo.temp, 1) if meteo.temp else None
            umidade = round(meteo.umd, 0) if meteo.umd else None
            vento = round(meteo.vel * 3.6, 1) if meteo.vel else 0
        else:
            temperatura = None
            umidade = None
            vento = 0
    except:
        temperatura = None
        umidade = None
        vento = 0

    # Precipitacao
    try:
        pluv = DadosPlv.objects.order_by('-data_t').first()
        precipitacao = round(pluv.chuva_1, 1) if pluv and pluv.chuva_1 else 0
    except:
        precipitacao = 0

    context = {
        # Estagio
        'estagio': estagio,
        'estagio_label': estagio_label,

        # Ocorrencias
        'ocorrencias': ocorrencias,
        'ocorrencias_count': ocorrencias_count,
        'ocorrencias_hoje': ocorrencias_hoje,
        'ocorrencias_criticas': 0,

        # Eventos
        'eventos_count': eventos_count,
        'eventos_semana': eventos_semana,
        'eventos_grandes': 0,

        # Sirenes
        'sirenes': sirenes,
        'sirenes_total': sirenes_total,
        'sirenes_acionadas': sirenes_acionadas,
        'sirenes_operantes': sirenes_operantes,

        # Calor
        'calor_index': calor_index,
        'calor_label': calor_label,
        'calor_status': 'NORMAL' if calor_index < 2 else 'ALERTA',

        # Meteorologia
        'temperatura': temperatura,
        'umidade': umidade,
        'vento': vento,
        'precipitacao': precipitacao,
        'meteo_nivel': 'N0',
        'meteo_status': 'ESTAVEL',
        'meteo_desc': 'Tempo Estavel',

        # Mobilidade
        'mobilidade_nivel': 'N1',
        'mobilidade_status': 'NORMAL',
        'mobilidade_desc': 'Transito Normal',
        'waze_alerts': 0,
        'vias_impactadas': 0,

        # Cameras
        'cameras_online': 0,
        'cameras_total': 0,
        'cameras_offline': 0,

        # Notificacoes
        'notifications_count': 0,
    }

    return render(request, 'cor_dashboard_hightech.html', context)



@api_view(['GET'])
def pluviometros_view(request):
    """API de pluviômetros - VERSÃO CORRIGIDA"""
    try:
        from aplicativo.models import DadosPlv
        from django.utils import timezone
        from datetime import datetime
        
        hoje = timezone.now().date()
        inicio = timezone.make_aware(datetime.combine(hoje, datetime.min.time()))
        fim = timezone.make_aware(datetime.combine(hoje, datetime.max.time()))
        
        leituras = DadosPlv.objects.filter(
            data_t__gte=inicio,
            data_t__lte=fim
        ).select_related('estacao')
        
        dados = {}
        for l in leituras:
            if l.estacao.id_e not in dados:
                dados[l.estacao.id_e] = {
                    'id': l.estacao.id,
                    'nome': l.estacao.nome,
                    'lat': float(l.estacao.lat or 0),
                    'lng': float(l.estacao.lon or 0),
                    'chuva_1h': float(l.chuva_1 or 0),
                    'chuva_4h': float(l.chuva_4 or 0),
                    'chuva_24h': float(l.chuva_24 or 0),
                    'chuva_96h': float(l.chuva_96 or 0),
                    'data': l.data_t.isoformat(),
                    'status': 'ativa'
                }
        
        return Response({
            'success': True,
            'data': list(dados.values()),
            'count': len(dados),
            'filtro': f'HOJE - {hoje}'
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
    

@api_view(['GET'])
def estacoes_vento_view(request):
    """API de Estações de Vento - Velocidade convertida para km/h"""
    try:
        data = []
        estacoes = EstacaoMet.objects.all()

        for estacao in estacoes:
            if estacao.lat and estacao.lon:
                ultimo = DadosMet.objects.filter(estacao=estacao).order_by('-data').first()

                if ultimo:
                    # ✅ Converter m/s → km/h (multiplicar por 3.6)
                    velocidade_ms = float(ultimo.vel or 0)
                    velocidade_kmh = round(velocidade_ms * 3.6, 1)  # Arredondar para 1 casa decimal
                    
                    data.append({
                        'id': estacao.id,
                        'nome': estacao.nome,
                        'lat': float(estacao.lat),
                        'lng': float(estacao.lon),
                        'temperatura': float(ultimo.temp or 0),
                        'umidade': float(ultimo.umd or 0),
                        'direcao': str(ultimo.dire) if ultimo.dire else 'N/A',
                        'velocidade': velocidade_kmh,  # ← Agora em km/h
                        'velocidade_ms': velocidade_ms,  # ← Original em m/s (opcional)
                        'data': str(ultimo.data) if ultimo.data else 'N/A',
                        'status': 'ativa'
                    })

        return Response({
            'success': True,
            'data': data,
            'count': len(data)
        })

    except Exception as e:
        import traceback
        logger.error(f'❌ Erro API ventos: {e}')
        print(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)


@api_view(['GET'])
def escolas_view(request):
    """API de Escolas Municipais"""
    print('DEBUG: escolas_view foi chamada!')
    escolas_list = list(EscolasMunicipais.objects.all())
    print(f'DEBUG: Encontradas {len(escolas_list)} escolas')

    data = []
    for escola in escolas_list:
        print(f'DEBUG: Processando {escola.nome} - x={escola.x}, y={escola.y}')
        data.append({
            'id': escola.id,
            'nome': escola.nome,
            'lat': float(escola.y),
            'lng': float(escola.x),
            'endereco': str(escola.endereco or 'N/A'),
            'bairro': str(escola.bairro or 'N/A'),
            'telefone': str(escola.telefone or 'N/A'),
            'tipo': 'escola_municipal'
        })

    print(f'DEBUG: Retornando {len(data)} escolas')
    return Response({'success': True, 'data': data, 'count': len(data)})


@api_view(['GET'])
def bens_tombados_view(request):
    """API de Bens Tombados"""
    try:
        data = []
        bens = BensProtegidos.objects.all()

        for bem in bens:
            if bem.y and bem.x:
                data.append({
                    'id': bem.id,
                    'nome': bem.np or 'Bem Tombado',
                    'lat': float(bem.y),
                    'lng': float(bem.x),
                    'rua': bem.rua or 'N/A',
                    'grau': bem.grau_de_pr or 'N/A',
                    'tipo': 'bem_tombado'
                })

        return Response({'success': True, 'data': data, 'count': len(data)})
    except Exception as e:
        return Response({'success': False, 'error': str(e), 'data': []}, status=500)


@api_view(['GET'])
def api_estagio(request):
    """API de estágio - formato novo"""
    try:
        # Buscar último estágio
        ultimo = Estagio.objects.filter(
            data_f__isnull=True
        ).order_by('-data_i').first()

        if not ultimo:
            ultimo = Estagio.objects.order_by('-data_i').first()

        if ultimo:
            # Extrair número do estágio
            estagio_texto = ultimo.esta or 'Nível 1'
            match = re.search(r'(\d+)', estagio_texto)
            nivel = int(match.group(1)) if match else 1

            # Mapear cores
            cores_map = {
                1: '#228d46',
                2: '#f5c520',
                3: '#ef8c3f',
                4: '#d0262d',
                5: '#5f2f7e'
            }

            descricoes_map = {
                1: 'Normalidade',
                2: 'Atenção',
                3: 'Alerta',
                4: 'Alerta Máximo',
                5: 'Crise'
            }

            return Response({
                'success': True,
                'data': {
                    'nivel': nivel,
                    'nome': estagio_texto,
                    'cor': cores_map.get(nivel, '#228d46'),
                    'descricao': descricoes_map.get(nivel, 'Normalidade')
                },
                'estagio': estagio_texto,
                'cor': cores_map.get(nivel, '#228d46'),
                'estagio_id': ultimo.id,
                'inicio': ultimo.data_i,
                'data_atualizacao': timezone.now()
            })

        # Se não tem estágio, retornar padrão
        return Response({
            'success': True,
            'data': {
                'nivel': 1,
                'nome': 'Nível 1',
                'cor': '#228d46',
                'descricao': 'Normalidade'
            },
            'estagio': 'Nível 1',
            'cor': '#228d46',
            'data_atualizacao': timezone.now()
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def inserir_ocorrencia_mobile(request):
    """
    Endpoint compatível com o sistema antigo
    Recebe via GET: ?lat=X&lon=Y&descricao=Z&tipo=W
    """
    try:
        ocorrencia = Ocorrencias.objects.create(
            incidente=request.GET.get('descricao', 'Ocorrência via mobile'),
            lat=request.GET.get('lat'),
            lon=request.GET.get('lon'),
            tipo_forma=request.GET.get('tipo', 'Outros'),
            prio=request.GET.get('prioridade', 'media'),
            bairro=request.GET.get('bairro', ''),
            status='Em andamento',
            data=timezone.now()
        )

        return Response({
            'success': True,
            'message': 'Ocorrência registrada',
            'id': ocorrencia.id
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)

@never_cache
def calor_api(request):
    """
    API de Alerta de Calor
    Retorna o alerta de calor atual
    """
    try:
        # Buscar último alerta ativo (sem data_f)
        alerta = Calor.objects.filter(data_f__isnull=True).latest('id')
        
        # Se não encontrar, buscar o último registro
        if not alerta:
            alerta = Calor.objects.latest('id')
        
        # Extrair número do texto "Nível X"
        nivel_texto = alerta.alive or 'Nível 0'
        match = re.search(r'(\d+)', nivel_texto)
        nivel = int(match.group(1)) if match else 0
        
        # Mapeamento de cores por nível
        cores_map = {
            0: '#228d46',  # Verde - Normal
            1: '#f5c520',  # Amarelo - Observação
            2: '#ef8c3f',  # Laranja - Atenção
            3: '#d0262d',  # Vermelho - Alerta
        }
        
        nomes_map = {
            0: 'Normal',
            1: 'Observação',
            2: 'Atenção',
            3: 'Alerta',
        }
        
        return JsonResponse({
            'success': True,
            'nivel': nivel,
            'nome': nomes_map.get(nivel, 'Normal'),
            'cor': cores_map.get(nivel, '#228d46'),
            'texto': nivel_texto,
            'data_inicio': alerta.data_i.isoformat() if alerta.data_i else None,
            'data_atualizacao': datetime.now().isoformat()
        })
        
    except Calor.DoesNotExist:
        return JsonResponse({
            'success': True,
            'nivel': 0,
            'nome': 'Normal',
            'cor': '#228d46',
            'texto': 'Nível 0',
            'data_inicio': None,
            'data_atualizacao': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def api_estagio_atual(request):
    """Retorna o estágio operacional calculado dinamicamente"""
    try:
        # Calcular inline
        CORES = {
            1: {'cor': '#228d46', 'nome': 'Nível 1', 'descricao': 'Normalidade'},
            2: {'cor': '#f5c520', 'nome': 'Nível 2', 'descricao': 'Atenção'},
            3: {'cor': '#ef8c3f', 'nome': 'Nível 3', 'descricao': 'Alerta'},
            4: {'cor': '#d0262d', 'nome': 'Nível 4', 'descricao': 'Alerta Máximo'},
            5: {'cor': '#5f2f7e', 'nome': 'Nível 5', 'descricao': 'Crise'}
        }

        # Nível Ocorrências
        abertas = Ocorrencias.objects.count()
        if abertas >= 50:
            nivel_ocorrencias = 5
        elif abertas >= 30:
            nivel_ocorrencias = 4
        elif abertas >= 15:
            nivel_ocorrencias = 3
        elif abertas >= 5:
            nivel_ocorrencias = 2
        else:
            nivel_ocorrencias = 1

        # Nível Tempo (simplificado)
        nivel_tempo = 1

        # Nível Eventos
        nivel_eventos = 1

        # Nível geral
        nivel_geral = int((nivel_ocorrencias + nivel_tempo + nivel_eventos) / 3)

        resultado = {
            'nivel': nivel_geral,
            'cor': CORES[nivel_geral]['cor'],
            'nome': CORES[nivel_geral]['nome'],
            'descricao': CORES[nivel_geral]['descricao'],
            'detalhes': {
                'tempo': {'nivel': nivel_tempo, **CORES[nivel_tempo]},
                'ocorrencias': {'nivel': nivel_ocorrencias, **CORES[nivel_ocorrencias], 'total': abertas},
                'eventos': {'nivel': nivel_eventos, **CORES[nivel_eventos]}
            }
        }

        return Response({
            'success': True,
            'data': resultado
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def waze_data_view(request):
    """Busca dados do Waze (alertas e congestionamentos)"""
    try:
        import requests
        
        url = "https://www.waze.com/row-partnerhub-api/partners/14420996249/waze-feeds/c5c19146-e0f9-44a7-9815-3862c8a6ed67?format=1"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return Response({
                'success': False,
                'error': 'Erro ao buscar dados do Waze'
            }, status=500)
        
        data = response.json()
        
        # Processar alertas
        alertas_processados = []
        for alert in data.get('alerts', [])[:100]:  # Limitar a 100 para performance
            tipo_map = {
                'HAZARD': 'Perigo',
                'ACCIDENT': 'Acidente',
                'JAM': 'Congestionamento',
                'WEATHERHAZARD': 'Condição Climática',
                'ROAD_CLOSED': 'Via Fechada'
            }
            
            subtipo_map = {
                'HAZARD_ON_ROAD_POT_HOLE': 'Buraco',
                'HAZARD_ON_ROAD_OBJECT': 'Objeto na Pista',
                'HAZARD_ON_ROAD': 'Perigo na Pista',
                'HAZARD_ON_SHOULDER': 'Perigo no Acostamento',
                'HAZARD_WEATHER': 'Clima',
                'HAZARD_ON_ROAD_ICE': 'Pista Escorregadia',
                'HAZARD_ON_ROAD_CONSTRUCTION': 'Obra',
                'HAZARD_ON_ROAD_CAR_STOPPED': 'Veículo Parado',
                'HAZARD_ON_ROAD_TRAFFIC_LIGHT_FAULT': 'Semáforo com Defeito'
            }
            
            alertas_processados.append({
                'id': alert.get('uuid'),
                'tipo': tipo_map.get(alert.get('type'), alert.get('type')),
                'subtipo': subtipo_map.get(alert.get('subtype'), alert.get('subtype', '')),
                'lat': alert.get('location', {}).get('y'),
                'lng': alert.get('location', {}).get('x'),
                'rua': alert.get('street', 'Via não identificada'),
                'cidade': alert.get('city', 'Rio de Janeiro'),
                'confianca': alert.get('confidence', 0),
                'confiabilidade': alert.get('reliability', 0),
                'data': alert.get('pubMillis')
            })
        
        # Processar congestionamentos
        jams_processados = []
        for jam in data.get('jams', [])[:50]:  # Limitar a 50
            # Pegar primeiro e último ponto da linha
            line = jam.get('line', [])
            if len(line) > 0:
                inicio = line[0]
                fim = line[-1]
                
                # Calcular ponto central
                centro_lat = (inicio['y'] + fim['y']) / 2
                centro_lng = (inicio['x'] + fim['x']) / 2
                
                nivel_map = {
                    0: 'Livre',
                    1: 'Leve',
                    2: 'Moderado', 
                    3: 'Pesado',
                    4: 'Parado',
                    5: 'Muito Lento'
                }
                
                jams_processados.append({
                    'id': jam.get('uuid'),
                    'rua': jam.get('street', 'Via não identificada'),
                    'cidade': jam.get('city', 'Rio de Janeiro'),
                    'nivel': jam.get('level', 0),
                    'nivel_texto': nivel_map.get(jam.get('level', 0), 'Desconhecido'),
                    'velocidade': round(jam.get('speedKMH', 0), 1),
                    'comprimento': jam.get('length', 0),
                    'atraso': jam.get('delay', 0),
                    'lat': centro_lat,
                    'lng': centro_lng,
                    'linha': line,  # Pontos para desenhar linha no mapa
                    'data': jam.get('pubMillis')
                })
        
        return Response({
            'success': True,
            'alertas': alertas_processados,
            'congestionamentos': jams_processados,
            'total_alertas': len(data.get('alerts', [])),
            'total_jams': len(data.get('jams', [])),
            'atualizacao': data.get('endTime')
        })
        
    except Exception as e:
        import traceback
        return Response({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
        
@csrf_exempt
def api_ocorrencias(request):
    """
    API de ocorrências - APENAS DE HOJE
    """
    try:
        from django.utils import timezone
        from datetime import datetime
        
        # FILTRAR APENAS HOJE
        hoje = timezone.now().date()
        inicio_dia = timezone.make_aware(datetime.combine(hoje, datetime.min.time()))
        fim_dia = timezone.make_aware(datetime.combine(hoje, datetime.max.time()))
        
        # MOSTRAR TODAS AS ABERTAS
        ocorrencias = Ocorrencias.objects.exclude(
        status='Concluído'
        ).order_by('-data')
        
        total = ocorrencias.count()
        
        # Cores
        cores_prioridade = {
            'SECUNDÁRIO': '#10b981',
            'BAIXO': '#10b981',
            'MEDIO': '#f59e0b',
            'ALTO': '#ef4444',
            'CRITICO': '#991b1b',
        }
        
        # Ícones
        icones = {
            'ACIDENTE': 'bi-car-front-fill',
            'ALAGAMENTO': 'bi-water',
            'DESLIZAMENTO': 'bi-exclamation-triangle-fill',
            'QUEDA': 'bi-tree-fill',
            'INCÊNDIO': 'bi-fire',
            'VAZAMENTO': 'bi-droplet-fill',
            'BURACO': 'bi-sign-stop-fill',
        }
        
        data = []
        for occ in ocorrencias:
            # Determinar ícone
            icone = 'bi-exclamation-circle-fill'
            if occ.incidente:
                for key, icon in icones.items():
                    if key in occ.incidente.upper():
                        icone = icon
                        break
            
            data.append({
                'id': occ.id,
                'id_c': occ.id_c or '',
                'tipo': occ.incidente or 'Outros',
                'descricao': occ.obs or 'Sem descrição',
                'endereco': occ.log or 'Endereço não informado',
                'bairro': occ.bairro or '',
                'lat': float(occ.lat) if occ.lat else None,
                'lng': float(occ.lon) if occ.lon else None,
                'prioridade': occ.prio or 'MEDIO',
                'cor_prioridade': cores_prioridade.get(occ.prio, '#6b7280'),
                'status': occ.status or 'Acionado',
                'icone': icone,
                'data_criacao': occ.data.isoformat() if occ.data else None,
            })
        
        abertas = ocorrencias.exclude(status='Concluído').count()
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': total,
            'abertas': abertas,
            'filtro': 'HOJE - ' + hoje.isoformat(),
        })
        
    except Exception as e:
        logger.error(f'Erro: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)
    


# ============================================
# API OCORRÊNCIAS - TEMPO REAL (HEXAGON)
# ============================================

@csrf_exempt
def api_ocorrencias_tempo_real(request):
    """
    API de ocorrências - BUSCA DIRETO DA API HEXAGON EM TEMPO REAL
    Retorna apenas ocorrências ABERTAS de HOJE
    """
    import requests
    from datetime import datetime, date
    from django.utils import timezone
    
    HEXAGON_API_BASE_URL = "https://api.corio-oncall.com.br/hxgnEvents/api"
    HEXAGON_API_USERNAME = "APIOpenedEvent"
    HEXAGON_API_PASSWORD = "12345"
    
    # Mapeamento de tipos de eventos
    EVENT_DICT = {
        "POP01": "ACIDENTE SEM VITIMA",
        "POP02": "ACIDENTE COM VITIMA",
        "POP03": "ACIDENTE COM OBITO",
        "POP04": "INCENDIO EM VEICULO",
        "POP05": "BOLSAO DE AGUA EM VIA",
        "POP06": "MANIFESTACAO EM LOCAL PUBLICO",
        "POP07": "INCENDIO EM IMOVEL",
        "POP08": "SINAIS DE TRANSITO COM MAU FUNCIONAMENTO",
        "POP09": "REINTEGRACAO DE POSSE",
        "POP10": "QUEDA DE ARVORE",
        "POP11": "QUEDA DE POSTE",
        "POP12": "ACIDENTE COM QUEDA DE CARGA",
        "POP13": "INCENDIO NO ENTORNO DE VIAS PUBLICAS",
        "POP14": "INCENDIO DENTRO DE TUNEIS",
        "POP15": "VAZAMENTO DE AGUA E ESGOTO",
        "POP16": "FALTA CRITICA DE ENERGIA OU APAGAO",
        "POP17": "IMPLOSAO",
        "POP18": "ESCAPAMENTO DE GAS",
        "POP19": "EVENTO NAO PROGRAMADO",
        "POP20": "ATROPELAMENTO",
        "POP21": "AFUNDAMENTO DE PISTA OU BURACO NA VIA",
        "POP22": "ABALROAMENTO",
        "POP23": "OBRA/MANUTENÇÃO EM LOCAL PUBLICO",
        "POP24": "OPERACAO POLICIAL",
        "POP25": "ACIONAMENTO DE SIRENES",
        "POP26": "ALAGAMENTO",
        "POP27": "ENCHENTE OU INUNDACAO",
        "POP28": "LAMINA DE AGUA",
        "POP29": "ACIDENTE AMBIENTAL",
        "POP30": "INCIDENTE COM BUEIRO",
        "POP31": "QUEDA DE ARVORE SOBRE FIACAO",
        "POP32": "RESIDUOS NA VIA",
        "POP33": "INCENDIO EM VEGETACAO",
        "POP34": "DESLIZAMENTO",
        "POP35": "QUEDA DE ESTRUTURA DE ALVENARIA",
        "POP36": "RESGATE OU REMOCAO DE ANIMAIS TERRESTRES E AEREOS",
        "POP37": "REMOCAO DE ANIMAIS MORTOS NA AREIA",
        "POP38": "RESGATE DE ANIMAL MARINHO PRESO EM REDE OU ENCALHADO",
        "POP39": "ANIMAL EM LOCAL PUBLICO",
        "POP40": "QUEDA DE CARGA VIVA DE GRANDE PORTE",
        "POP41": "QUEDA DE CARGA VIVA DE PEQUENO PORTE",
        "POP42": "PROTOCOLO DE VIA",
        "POP43": "PROTOCOLO DE CICLOVIA",
        "POP44": "ENGUICO NA VIA",
        "POP45": "PROTOCOLO DE CALOR - NC2",
        "POP46": "PROTOCOLO DE CALOR - NC3",
        "POP47": "PROTOCOLO DE CALOR - NC4",
        "POP48": "PROTOCOLO DE CALOR - NC5",
        "POP49": "PROTOCOLO DE PARQUES",
        "POP50": "OCORRENCIA EM PARQUE AEROPORTUARIO",
        "POP51": "INTERRUPÇÃO PARCIAL OU TOTAL DE MODAL DE TRANSPORTE",
        "POP52": "FIAÇÃO PARTIDA/ARREADA",
        "POP53": "RESSACA/MARÉ ALTA"
    }
    
    PRIORIDADE_DICT = {
        1: "BAIXA",
        2: "MÉDIA",
        3: "ALTA",
        4: "MUITO ALTA"
    }
    
    CORES_PRIORIDADE = {
        'BAIXA': '#10b981',
        'MÉDIA': '#f59e0b',
        'ALTA': '#ef4444',
        'MUITO ALTA': '#991b1b',
    }
    
    ICONES = {
        'ACIDENTE': 'bi-car-front-fill',
        'ALAGAMENTO': 'bi-water',
        'DESLIZAMENTO': 'bi-exclamation-triangle-fill',
        'QUEDA': 'bi-tree-fill',
        'INCENDIO': 'bi-fire',
        'INCÊNDIO': 'bi-fire',
        'VAZAMENTO': 'bi-droplet-fill',
        'BURACO': 'bi-sign-stop-fill',
        'AFUNDAMENTO': 'bi-sign-stop-fill',
    }
    
    try:
        # 1. AUTENTICAR NA API HEXAGON
        auth_url = f"{HEXAGON_API_BASE_URL}/Events/Login"
        auth_payload = {"UserName": HEXAGON_API_USERNAME, "Password": HEXAGON_API_PASSWORD}
        
        auth_response = requests.post(auth_url, json=auth_payload, timeout=10)
        auth_response.raise_for_status()
        
        token = auth_response.json().get("AccessToken")
        if not token:
            raise Exception("Falha na autenticação - Token não recebido")
        
        # 2. BUSCAR OCORRÊNCIAS ABERTAS
        events_url = f"{HEXAGON_API_BASE_URL}/Events/OpenedEvents"
        events_payload = {"token": token}
        
        events_response = requests.post(events_url, json=events_payload, timeout=15)
        events_response.raise_for_status()
        
        raw_events = events_response.json()
        
        # 3. FILTRAR APENAS AS DE HOJE
        hoje = date.today()
        
        ocorrencias = []
        for item in raw_events:
            # Pegar data do evento
            created_date = item.get("CreatedDate", "")
            if not created_date:
                continue
            
            try:
                # Parse da data (formato: 2025-11-24T10:30:00)
                dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                event_date = dt.date()
                
                # Filtrar apenas de HOJE
                if event_date != hoje:
                    continue
                    
            except Exception:
                continue
            
            # Pegar tipo do evento
            tipo_code = item.get("AgencyEventTypeCode", "")
            tipo = EVENT_DICT.get(tipo_code, tipo_code or "OUTROS")
            
            # Pegar prioridade
            prio_num = item.get("Priority", 1)
            prioridade = PRIORIDADE_DICT.get(prio_num, "MÉDIA")
            
            # Determinar ícone
            icone = 'bi-exclamation-circle-fill'
            for key, icon in ICONES.items():
                if key in tipo.upper():
                    icone = icon
                    break
            
            ocorrencias.append({
                'id': item.get("EventId"),
                'id_c': item.get("EventId"),
                'tipo': tipo,
                'descricao': item.get("Description") or tipo,
                'endereco': item.get("Location") or 'Endereço não informado',
                'bairro': item.get("District") or '',
                'lat': item.get("Latitude"),
                'lng': item.get("Longitude"),
                'prioridade': prioridade,
                'cor_prioridade': CORES_PRIORIDADE.get(prioridade, '#6b7280'),
                'status': 'Em andamento',
                'icone': icone,
                'data_criacao': created_date,
            })
        
        # Ordenar por data (mais recentes primeiro)
        ocorrencias.sort(key=lambda x: x['data_criacao'] or '', reverse=True)
        
        total = len(ocorrencias)
        
        return JsonResponse({
            'success': True,
            'data': ocorrencias,
            'count': total,
            'abertas': total,
            'filtro': f'HOJE (TEMPO REAL) - {hoje.isoformat()}',
            'fonte': 'API Hexagon',
            'timestamp': timezone.now().isoformat()
        })
        
    except requests.exceptions.Timeout:
        logger.error('Timeout ao conectar com API Hexagon')
        return JsonResponse({
            'success': False,
            'error': 'Timeout ao conectar com API Hexagon',
            'data': []
        }, status=504)
        
    except Exception as e:
        logger.error(f'Erro ao buscar ocorrências tempo real: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)
    
# ===== MATRIZ DECISÓRIA =====
def matriz_decisoria(request):
    return render(request, 'mapa_novo/matriz_decisoria.html')

def api_matriz_decisoria(request):
    # SUBSTITUA PELA SUA API REAL!
    # response = requests.get('SUA_URL_API')
    # return JsonResponse(response.json())
    
    # Dados de exemplo por enquanto
    dados = {
        "EstagioOperacional": {"EstagioOperacionalSugerido": 1, "ProgressoEstagioOperacionalSugerido": 30, "ValorEstagioOperacionalSugerido": 0.36},
        "NivelIndicado": {"NivelG1": 1, "NivelG2": 0, "NivelG3": 0, "NivelG4": 0, "ProximidadeNivelSeguinte": 27.5},
        "NivelG1": {"TabelaNivelG1": {"ProgressoNivelG1": 100, "NivelCalor": 1, "Chuva": {"Total": "116", "ChuvaFraca": "4", "ChuvaModerada": "0", "ChuvaForte": "0", "ChuvaMuitoForte": "0"}, "Sirene": {"Total": "162", "Alarmada": "0"}, "Vento": {"VentoForte": "0", "VentoMuitoForte": "0", "VentoMediaH01": "8.6"}}},
        "NivelG2": {"ProgressoNivelG2": 73, "Critica": 0, "MuitoAlta": 0, "Alta": 0, "Media": 1, "Baixa": 11},
        "NivelG3": {"ProgressoNivelG3": 0, "StatusModal": {"Metrô": "Normal", "BRT": "Normal", "Trem": "Normal", "Ônibus": "Normal", "Barcas": "Normal", "VLT": "Normal", "GIG": "Normal", "SDU": "Normal"}, "Transito": {"EAC": 49}, "Modal": {"ModalEmAtencao": 0, "ModalInterrompido": 0}},
        "NivelG4": {"ProgressoNivelG4": 0, "MuitoAlta": 0, "Alta": 0, "Media": 0, "Baixa": 0, "Evento": None}
    }
    return JsonResponse(dados)

# FUNÇÕES DUPLICADAS matriz_decisoria e api_matriz_decisoria REMOVIDAS
# Já definidas anteriormente no arquivo

@api_view(['GET'])
def api_cameras(request):
    """API de câmeras de monitoramento"""
    try:
        from aplicativo.models import Cameras
        
        # Parâmetros
        bairro = request.GET.get('bairro', None)
        status = request.GET.get('status', None)
        search = request.GET.get('search', None)
        
        # Query
        cameras = Cameras.objects.all()
        
        # Filtros
        if bairro:
            cameras = cameras.filter(bairro__icontains=bairro)
        
        if status:
            cameras = cameras.filter(status__iexact=status)
        
        if search:
            cameras = cameras.filter(nome__icontains=search)
        
        # Serializar
        data = []
        bairros_set = set()
        
        for cam in cameras.order_by('id_c'):
            try:
                lat = float(cam.lat) if cam.lat else None
                lon = float(cam.lon) if cam.lon else None
                
                if lat and lon and lat != 0 and lon != 0:
                    data.append({
                        'id': cam.id,
                        'id_c': cam.id_c,
                        'nome': cam.nome or f'Câmera {cam.id_c}',
                        'bairro': cam.bairro or 'Sem bairro',
                        'lat': lat,
                        'lng': lon,
                        'status': cam.status,
                        'url_stream': f'https://dev.tixxi.rio/outvideo2/?CODE={cam.id_c}&KEY=H4281'
                    })
                    bairros_set.add(cam.bairro or 'Sem bairro')
            except:
                continue
        
        return Response({
            'success': True,
            'data': data,
            'count': len(data),
            'bairros': sorted(list(bairros_set))
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def api_sirenes(request):
    """API de sirenes"""
    try:
        from aplicativo.models import Sirene
        
        sirenes = Sirene.objects.all()
        data = []
        
        for s in sirenes:
            try:
                data.append({
                    'id': s.id,
                    'nome': s.nome or f'Sirene {s.id}',
                    'endereco': s.endereco if hasattr(s, 'endereco') else '',
                    'bairro': s.bairro if hasattr(s, 'bairro') else '',
                    'lat': float(s.lat) if s.lat else None,
                    'lng': float(s.lon) if s.lon else None,
                    'status': s.status if hasattr(s, 'status') else 'inativa',
                    'prioridade': s.prioridade if hasattr(s, 'prioridade') else 'média'
                })
            except:
                continue
        
        return Response({'success': True, 'data': data, 'count': len(data)})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def api_pluviometros(request):
    """API de pluviômetros - VERSÃO TESTE SIMPLES"""
    
    # ✅ RETORNAR DADOS FAKE PRIMEIRO PARA TESTAR
    return Response({
        'success': True,
        'data': [
            {
                'id': 1,
                'nome': 'Teste Tijuca',
                'lat': -22.9249,
                'lng': -43.2311,
                'chuva_1h': 5.5,
                'chuva_4h': 10.0,
                'chuva_24h': 20.0,
                'chuva_96h': 40.0,
                'data': '2025-11-13T12:00:00',
                'status': 'ativa'
            }
        ],
        'count': 1,
        'chovendo': 1,
        'filtro': 'TESTE',
        'mensagem': '🔥 FUNÇÃO FUNCIONANDO!'
    })


@api_view(['GET'])
def api_ventos(request):
    """API de estações meteorológicas"""
    try:
        from aplicativo.models import EstacaoMet
        
        estacoes = EstacaoMet.objects.all()
        data = []
        
        for e in estacoes:
            try:
                data.append({
                    'id': e.id,
                    'nome': e.nome if hasattr(e, 'nome') else f'Estação {e.id}',
                    'lat': float(e.lat) if hasattr(e, 'lat') and e.lat else None,
                    'lng': float(e.lon) if hasattr(e, 'lon') and e.lon else None,
                    'velocidade': float(e.velocidade) if hasattr(e, 'velocidade') and e.velocidade else 0,
                    'direcao': e.direcao if hasattr(e, 'direcao') else 'N/A',
                    'temperatura': float(e.temperatura) if hasattr(e, 'temperatura') and e.temperatura else 0,
                    'umidade': float(e.umidade) if hasattr(e, 'umidade') and e.umidade else 0,
                    'data': e.data.strftime('%d/%m/%Y %H:%M') if hasattr(e, 'data') and e.data else 'N/A'
                })
            except:
                continue
        
        return Response({'success': True, 'data': data, 'count': len(data)})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


# ===== VIEWS DE METEOROLOGIA =====

@login_required(login_url='login')
@never_cache
def meteorologia_dashboard_view(request):
    """Dashboard de Meteorologia"""
    return render(request, 'mapa_novo/meteorologia_dashboard.html')


@api_view(['GET'])
def api_previsao_tempo(request):
    """API de previsão do tempo (dados simulados por enquanto)"""
    try:
        # Dados de previsão para próximos 5 dias
        previsao = [
            {
                'dia': 'Segunda',
                'data': '28/10',
                'temp_min': 22,
                'temp_max': 28,
                'condicao': 'Parcialmente nublado',
                'icone': 'cloud-sun',
                'chuva_prob': 30,
                'umidade': 65
            },
            {
                'dia': 'Terça',
                'data': '29/10',
                'temp_min': 21,
                'temp_max': 27,
                'condicao': 'Chuva leve',
                'icone': 'cloud-drizzle',
                'chuva_prob': 70,
                'umidade': 75
            },
            {
                'dia': 'Quarta',
                'data': '30/10',
                'temp_min': 20,
                'temp_max': 26,
                'condicao': 'Nublado',
                'icone': 'cloud',
                'chuva_prob': 50,
                'umidade': 70
            },
            {
                'dia': 'Quinta',
                'data': '31/10',
                'temp_min': 23,
                'temp_max': 29,
                'condicao': 'Ensolarado',
                'icone': 'sun',
                'chuva_prob': 10,
                'umidade': 55
            },
            {
                'dia': 'Sexta',
                'data': '01/11',
                'temp_min': 24,
                'temp_max': 30,
                'condicao': 'Ensolarado',
                'icone': 'sun',
                'chuva_prob': 5,
                'umidade': 50
            }
        ]
        
        return Response({
            'success': True,
            'data': previsao
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def api_historico_chuva(request):
    """API de histórico de chuva - últimas 24 horas"""
    try:
        from aplicativo.models import DadosPlv
        from datetime import datetime, timedelta
        
        # Pegar dados das últimas 24 horas
        data_limite = datetime.now() - timedelta(hours=24)
        
        dados = DadosPlv.objects.filter(
            data__gte=data_limite
        ).order_by('data')[:100]
        
        historico = []
        for d in dados:
            historico.append({
                'hora': d.data.strftime('%H:%M') if d.data else 'N/A',
                'chuva_1h': float(d.chuva_1 or 0),
                'estacao': d.estacao.nome if hasattr(d, 'estacao') else 'N/A'
            })
        
        return Response({
            'success': True,
            'data': historico
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)


@api_view(['GET'])
def api_alertas_meteorologicos(request):
    """API de alertas meteorológicos ativos"""
    try:
        from aplicativo.models import EstacaoPlv, DadosPlv
        
        alertas = []
        
        # Verificar estações com chuva forte
        estacoes = EstacaoPlv.objects.all()
        
        for estacao in estacoes:
            ultimo = DadosPlv.objects.filter(estacao=estacao).order_by('-data').first()
            
            if ultimo:
                chuva_1h = float(ultimo.chuva_1 or 0)
                
                if chuva_1h >= 25:
                    alertas.append({
                        'tipo': 'Chuva Forte',
                        'nivel': 'alto',
                        'estacao': estacao.nome,
                        'valor': chuva_1h,
                        'mensagem': f'Chuva forte de {chuva_1h}mm em {estacao.nome}',
                        'icone': 'cloud-rain-heavy'
                    })
                elif chuva_1h >= 10:
                    alertas.append({
                        'tipo': 'Chuva Moderada',
                        'nivel': 'medio',
                        'estacao': estacao.nome,
                        'valor': chuva_1h,
                        'mensagem': f'Chuva moderada de {chuva_1h}mm em {estacao.nome}',
                        'icone': 'cloud-rain'
                    })
        
        return Response({
            'success': True,
            'data': alertas,
            'count': len(alertas)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)

# ===== VIEWS DE MOBILIDADE URBANA =====

@login_required(login_url='login')
@never_cache
def mobilidade_dashboard_view(request):
    """Dashboard de Mobilidade Urbana"""
    return render(request, 'mapa_novo/mobilidade_dashboard.html')


@api_view(['GET'])
def api_brt_linhas(request):
    """API de linhas de BRT"""
    try:
        # Dados das principais linhas de BRT do Rio
        linhas = [
            {
                'id': 1,
                'nome': 'TransOeste',
                'cor': '#0066cc',
                'status': 'Operação Normal',
                'status_code': 'normal',
                'estacoes': 59,
                'extensao': '56 km',
                'tempo_medio': '85 min',
                'intervalo': '5-10 min'
            },
            {
                'id': 2,
                'nome': 'TransCarioca',
                'cor': '#ff6600',
                'status': 'Operação Normal',
                'status_code': 'normal',
                'estacoes': 45,
                'extensao': '39 km',
                'tempo_medio': '60 min',
                'intervalo': '4-8 min'
            },
            {
                'id': 3,
                'nome': 'TransOlímpica',
                'cor': '#00cc66',
                'status': 'Operação Normal',
                'status_code': 'normal',
                'estacoes': 18,
                'extensao': '26 km',
                'tempo_medio': '35 min',
                'intervalo': '6-12 min'
            },
            {
                'id': 4,
                'nome': 'TransBrasil',
                'cor': '#cc0000',
                'status': 'Em Obras',
                'status_code': 'obras',
                'estacoes': 28,
                'extensao': '32 km',
                'tempo_medio': 'N/A',
                'intervalo': 'N/A'
            }
        ]
        
        return Response({
            'success': True,
            'data': linhas,
            'count': len(linhas)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def api_metro_linhas(request):
    """API de linhas de Metrô"""
    try:
        linhas = [
            {
                'id': 1,
                'numero': '1',
                'nome': 'Linha 1 (Laranja)',
                'cor': '#ff6600',
                'status': 'Operação Normal',
                'status_code': 'normal',
                'estacoes': 19,
                'extensao': '19,8 km',
                'intervalo': '3-5 min',
                'origem': 'Uruguai',
                'destino': 'General Osório'
            },
            {
                'id': 2,
                'numero': '2',
                'nome': 'Linha 2 (Verde)',
                'cor': '#00aa00',
                'status': 'Operação Normal',
                'status_code': 'normal',
                'estacoes': 18,
                'extensao': '22,8 km',
                'intervalo': '4-6 min',
                'origem': 'Pavuna',
                'destino': 'Botafogo'
            },
            {
                'id': 3,
                'numero': '4',
                'nome': 'Linha 4 (Amarela)',
                'cor': '#ffcc00',
                'status': 'Operação Normal',
                'status_code': 'normal',
                'estacoes': 6,
                'extensao': '16 km',
                'intervalo': '5-8 min',
                'origem': 'Ipanema',
                'destino': 'Jardim Oceânico'
            }
        ]
        
        return Response({
            'success': True,
            'data': linhas,
            'count': len(linhas)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def api_bike_rio(request):
    """API de estações Bike Rio"""
    try:
        # Dados simulados de estações Bike Rio
        estacoes = [
            {
                'id': 1,
                'nome': 'Copacabana - Posto 5',
                'bairro': 'Copacabana',
                'bikes_disponiveis': 12,
                'vagas_disponiveis': 8,
                'total_vagas': 20,
                'status': 'Operando',
                'lat': -22.9876,
                'lng': -43.1902
            },
            {
                'id': 2,
                'nome': 'Ipanema - Posto 9',
                'bairro': 'Ipanema',
                'bikes_disponiveis': 5,
                'vagas_disponiveis': 15,
                'total_vagas': 20,
                'status': 'Operando',
                'lat': -22.9833,
                'lng': -43.2043
            },
            {
                'id': 3,
                'nome': 'Leblon - Posto 12',
                'bairro': 'Leblon',
                'bikes_disponiveis': 0,
                'vagas_disponiveis': 18,
                'total_vagas': 18,
                'status': 'Sem Bikes',
                'lat': -22.9844,
                'lng': -43.2200
            },
            {
                'id': 4,
                'nome': 'Botafogo - Metrô',
                'bairro': 'Botafogo',
                'bikes_disponiveis': 18,
                'vagas_disponiveis': 2,
                'total_vagas': 20,
                'status': 'Operando',
                'lat': -22.9519,
                'lng': -43.1822
            },
            {
                'id': 5,
                'nome': 'Centro - Praça XV',
                'bairro': 'Centro',
                'bikes_disponiveis': 7,
                'vagas_disponiveis': 13,
                'total_vagas': 20,
                'status': 'Operando',
                'lat': -22.9035,
                'lng': -43.1737
            }
        ]
        
        return Response({
            'success': True,
            'data': estacoes,
            'count': len(estacoes),
            'total_bikes': sum(e['bikes_disponiveis'] for e in estacoes),
            'total_vagas': sum(e['total_vagas'] for e in estacoes)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def api_transito_status(request):
    """API de status geral do trânsito"""
    try:
        # Status simulado baseado em horário
        from datetime import datetime
        
        hora_atual = datetime.now().hour
        
        # Definir status baseado no horário
        if (7 <= hora_atual <= 9) or (17 <= hora_atual <= 19):
            nivel = 3  # Intenso
            descricao = 'Trânsito Intenso'
            cor = '#ef4444'
        elif (10 <= hora_atual <= 16) or (20 <= hora_atual <= 22):
            nivel = 2  # Moderado
            descricao = 'Trânsito Moderado'
            cor = '#f59e0b'
        else:
            nivel = 1  # Leve
            descricao = 'Trânsito Leve'
            cor = '#10b981'
        
        return Response({
            'success': True,
            'data': {
                'nivel': nivel,
                'descricao': descricao,
                'cor': cor,
                'hora': hora_atual,
                'lentidao_km': nivel * 15,  # km de lentidão
                'velocidade_media': 45 - (nivel * 10)  # km/h
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
        
        
def waze_alerts_api(request):
    """
    API compatível com o frontend - redireciona para waze_data_view
    """
    try:
        import requests
        
        # Usar a URL oficial do parceiro Waze do Rio
        url = "https://www.waze.com/row-partnerhub-api/partners/14420996249/waze-feeds/c5c19146-e0f9-44a7-9815-3862c8a6ed67?format=1"
        
        print('🚗 Buscando dados do Waze...')
        print(f'📡 URL: {url}')
        
        response = requests.get(url, timeout=15)
        
        print(f'✅ Status: {response.status_code}')
        
        if response.status_code != 200:
            return JsonResponse({
                'success': False,
                'error': f'Waze API retornou status {response.status_code}',
                'data': []
            })
        
        data = response.json()
        
        print(f'📦 Dados recebidos: {len(data.get("alerts", []))} alertas, {len(data.get("jams", []))} congestionamentos')
        
        # Processar alertas
        alerts = []
        
        for alert in data.get('alerts', []):
            alerts.append({
                'id': alert.get('uuid', ''),
                'type': alert.get('type', 'UNKNOWN'),
                'subtype': alert.get('subtype', ''),
                'location': {
                    'x': alert.get('location', {}).get('x'),
                    'y': alert.get('location', {}).get('y')
                },
                'street': alert.get('street', ''),
                'city': alert.get('city', ''),
                'reportDescription': alert.get('reportDescription', ''),
                'reliability': alert.get('reliability', 0),
                'confidence': alert.get('confidence', 0),
                'nThumbsUp': alert.get('nThumbsUp', 0),
                'pubMillis': alert.get('pubMillis', 0)
            })
        
        # Processar congestionamentos
        for jam in data.get('jams', []):
            line = jam.get('line', [])
            if line and len(line) > 0:
                mid_point = line[len(line) // 2]
                alerts.append({
                    'id': jam.get('uuid', ''),
                    'type': 'JAM',
                    'subtype': f"Nível {jam.get('level', 0)}",
                    'location': {
                        'x': mid_point.get('x'),
                        'y': mid_point.get('y')
                    },
                    'street': jam.get('street', ''),
                    'city': jam.get('city', ''),
                    'reportDescription': f"Congestionamento - Velocidade: {jam.get('speedKMH', 0)} km/h",
                    'reliability': jam.get('reliability', 0),
                    'confidence': 10,
                    'nThumbsUp': 0,
                    'pubMillis': jam.get('pubMillis', 0)
                })
        
        print(f'✅ Total de alertas processados: {len(alerts)}')
        
        return JsonResponse({
            'success': True,
            'data': alerts,
            'count': len(alerts),
            'timestamp': datetime.now().isoformat()
        })
        
    except requests.exceptions.Timeout:
        print('❌ Timeout!')
        return JsonResponse({
            'success': False,
            'error': 'Timeout ao conectar com Waze',
            'data': []
        })
    except Exception as e:
        print(f'❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': []
        })


@csrf_exempt
def chuva_api(request):
    """API de dados de chuva/pluviômetros"""
    try:
        # TODO: Substituir por dados reais do banco
        # Por enquanto, dados de exemplo
        
        pluviometros = [
            {
                'id': 1,
                'nome': 'Alto da Boa Vista',
                'lat': -22.9667,
                'lng': -43.2833,
                'chuva_15min': 12.5,
                'chuva_1h': 25.3,
                'chuva_24h': 45.8
            },
            {
                'id': 2,
                'nome': 'Tijuca',
                'lat': -22.9333,
                'lng': -43.2333,
                'chuva_15min': 8.2,
                'chuva_1h': 18.7,
                'chuva_24h': 32.4
            },
            {
                'id': 3,
                'nome': 'Copacabana',
                'lat': -22.9711,
                'lng': -43.1822,
                'chuva_15min': 2.1,
                'chuva_1h': 5.3,
                'chuva_24h': 12.7
            },
            {
                'id': 4,
                'nome': 'Barra da Tijuca',
                'lat': -23.0050,
                'lng': -43.3650,
                'chuva_15min': 0.5,
                'chuva_1h': 1.2,
                'chuva_24h': 3.8
            },
            {
                'id': 5,
                'nome': 'Jacarepaguá',
                'lat': -22.9211,
                'lng': -43.3628,
                'chuva_15min': 15.8,
                'chuva_1h': 32.4,
                'chuva_24h': 56.9
            },
            {
                'id': 6,
                'nome': 'Centro',
                'lat': -22.9068,
                'lng': -43.1729,
                'chuva_15min': 6.3,
                'chuva_1h': 14.5,
                'chuva_24h': 28.2
            },
        ]
        
        # Estatísticas gerais
        stats = {
            'temperatura_media': 25.3,
            'umidade_media': 68,
            'chuva_24h': sum(p['chuva_24h'] for p in pluviometros) / len(pluviometros),
            'vento_velocidade': 15
        }
        
        return JsonResponse({
            'success': True,
            'data': pluviometros,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def alertas_api(request):
    """API de alertas meteorológicos"""
    try:
        # TODO: Substituir por dados reais do banco
        # Por enquanto, dados de exemplo
        
        alertas = [
            {
                'id': 1,
                'tipo': 'chuva_forte',
                'severidade': 'alta',
                'titulo': 'Chuva Forte',
                'mensagem': 'Chuva forte prevista para as próximas horas',
                'regiao': 'Zona Norte',
                'lat': -22.9333,
                'lng': -43.2333
            },
            {
                'id': 2,
                'tipo': 'alagamento',
                'severidade': 'media',
                'titulo': 'Risco de Alagamento',
                'mensagem': 'Pontos de alagamento reportados',
                'regiao': 'Zona Sul',
                'lat': -22.9711,
                'lng': -43.1822
            }
        ]
        
        return JsonResponse({
            'success': True,
            'alertas': alertas,
            'total': len(alertas),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'alertas': []
        }, status=500)


@csrf_exempt
def estagio_api(request):
    """API de estágio operacional"""
    try:
        estagios = ['Normalidade', 'Atenção', 'Alerta', 'Crise', 'Mobilização']
        
        return JsonResponse({
            'success': True,
            'estagio': 'Atenção',
            'nivel': 2,
            'descricao': 'Chuva moderada em algumas regiões',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        

        
        
@csrf_exempt
def chuva_api(request):
    """API de dados de chuva/pluviômetros"""
    import random
    
    # 30 pluviômetros cobrindo toda a cidade do Rio
    pluviometros = [
        # ZONA NORTE
        {'id': 1, 'nome': 'Tijuca', 'lat': -22.9333, 'lng': -43.2333, 
         'chuva_15min': random.uniform(0, 15), 'chuva_1h': random.uniform(5, 30), 'chuva_24h': random.uniform(10, 50)},
        {'id': 2, 'nome': 'Maracanã', 'lat': -22.9122, 'lng': -43.2302, 
         'chuva_15min': random.uniform(0, 15), 'chuva_1h': random.uniform(5, 30), 'chuva_24h': random.uniform(10, 50)},
        {'id': 3, 'nome': 'São Cristóvão', 'lat': -22.8994, 'lng': -43.2228, 
         'chuva_15min': random.uniform(0, 15), 'chuva_1h': random.uniform(5, 30), 'chuva_24h': random.uniform(10, 50)},
        {'id': 4, 'nome': 'Méier', 'lat': -22.9025, 'lng': -43.2789, 
         'chuva_15min': random.uniform(0, 15), 'chuva_1h': random.uniform(5, 30), 'chuva_24h': random.uniform(10, 50)},
        {'id': 5, 'nome': 'Vila Isabel', 'lat': -22.9164, 'lng': -43.2456, 
         'chuva_15min': random.uniform(0, 15), 'chuva_1h': random.uniform(5, 30), 'chuva_24h': random.uniform(10, 50)},
        
        # ZONA SUL
        {'id': 6, 'nome': 'Copacabana', 'lat': -22.9711, 'lng': -43.1822, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 20), 'chuva_24h': random.uniform(5, 35)},
        {'id': 7, 'nome': 'Ipanema', 'lat': -22.9838, 'lng': -43.2096, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 20), 'chuva_24h': random.uniform(5, 35)},
        {'id': 8, 'nome': 'Leblon', 'lat': -22.9844, 'lng': -43.2175, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 20), 'chuva_24h': random.uniform(5, 35)},
        {'id': 9, 'nome': 'Botafogo', 'lat': -22.9519, 'lng': -43.1828, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 20), 'chuva_24h': random.uniform(5, 35)},
        {'id': 10, 'nome': 'Lagoa', 'lat': -22.9711, 'lng': -43.2053, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 20), 'chuva_24h': random.uniform(5, 35)},
        {'id': 11, 'nome': 'Gávea', 'lat': -22.9797, 'lng': -43.2344, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 20), 'chuva_24h': random.uniform(5, 35)},
        
        # CENTRO
        {'id': 12, 'nome': 'Centro', 'lat': -22.9068, 'lng': -43.1729, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(3, 25), 'chuva_24h': random.uniform(8, 40)},
        {'id': 13, 'nome': 'Praça XV', 'lat': -22.9033, 'lng': -43.1752, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(3, 25), 'chuva_24h': random.uniform(8, 40)},
        {'id': 14, 'nome': 'Lapa', 'lat': -22.9133, 'lng': -43.1786, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(3, 25), 'chuva_24h': random.uniform(8, 40)},
        
        # ZONA OESTE
        {'id': 15, 'nome': 'Barra da Tijuca', 'lat': -23.0050, 'lng': -43.3650, 
         'chuva_15min': random.uniform(0, 8), 'chuva_1h': random.uniform(1, 15), 'chuva_24h': random.uniform(3, 30)},
        {'id': 16, 'nome': 'Recreio', 'lat': -23.0197, 'lng': -43.4597, 
         'chuva_15min': random.uniform(0, 8), 'chuva_1h': random.uniform(1, 15), 'chuva_24h': random.uniform(3, 30)},
        {'id': 17, 'nome': 'Jacarepaguá', 'lat': -22.9211, 'lng': -43.3628, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(5, 28), 'chuva_24h': random.uniform(10, 55)},
        {'id': 18, 'nome': 'Cidade de Deus', 'lat': -22.9456, 'lng': -43.3592, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(5, 28), 'chuva_24h': random.uniform(10, 55)},
        {'id': 19, 'nome': 'Campo Grande', 'lat': -22.9009, 'lng': -43.5615, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(3, 22), 'chuva_24h': random.uniform(8, 45)},
        {'id': 20, 'nome': 'Bangu', 'lat': -22.8719, 'lng': -43.4664, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(3, 22), 'chuva_24h': random.uniform(8, 45)},
        
        # REGIÕES MONTANHOSAS (mais chuva)
        {'id': 21, 'nome': 'Alto da Boa Vista', 'lat': -22.9667, 'lng': -43.2833, 
         'chuva_15min': random.uniform(5, 25), 'chuva_1h': random.uniform(15, 45), 'chuva_24h': random.uniform(30, 80)},
        {'id': 22, 'nome': 'Floresta da Tijuca', 'lat': -22.9442, 'lng': -43.2633, 
         'chuva_15min': random.uniform(5, 25), 'chuva_1h': random.uniform(15, 45), 'chuva_24h': random.uniform(30, 80)},
        {'id': 23, 'nome': 'Vista Chinesa', 'lat': -22.9583, 'lng': -43.2361, 
         'chuva_15min': random.uniform(5, 25), 'chuva_1h': random.uniform(15, 45), 'chuva_24h': random.uniform(30, 80)},
        {'id': 24, 'nome': 'Corcovado', 'lat': -22.9519, 'lng': -43.2106, 
         'chuva_15min': random.uniform(5, 25), 'chuva_1h': random.uniform(15, 45), 'chuva_24h': random.uniform(30, 80)},
        
        # ILHA DO GOVERNADOR
        {'id': 25, 'nome': 'Ilha do Governador', 'lat': -22.8147, 'lng': -43.2108, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 18), 'chuva_24h': random.uniform(5, 35)},
        {'id': 26, 'nome': 'Galeão', 'lat': -22.8094, 'lng': -43.2436, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 18), 'chuva_24h': random.uniform(5, 35)},
        
        # SUBÚRBIOS
        {'id': 27, 'nome': 'Penha', 'lat': -22.8436, 'lng': -43.2775, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(4, 24), 'chuva_24h': random.uniform(10, 48)},
        {'id': 28, 'nome': 'Pavuna', 'lat': -22.8117, 'lng': -43.3539, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(4, 24), 'chuva_24h': random.uniform(10, 48)},
        {'id': 29, 'nome': 'Irajá', 'lat': -22.8328, 'lng': -43.3264, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(4, 24), 'chuva_24h': random.uniform(10, 48)},
        {'id': 30, 'nome': 'Santa Cruz', 'lat': -22.9197, 'lng': -43.6836, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(3, 20), 'chuva_24h': random.uniform(7, 42)},
    ]
    
    stats = {
        'temperatura_media': round(random.uniform(22, 28), 1),
        'umidade_media': random.randint(60, 85),
        'chuva_24h': round(sum(p['chuva_24h'] for p in pluviometros) / len(pluviometros), 1),
        'vento_velocidade': random.randint(10, 25)
    }
    
    return JsonResponse({
        'success': True,
        'data': pluviometros,
        'stats': stats,
        'timestamp': datetime.now().isoformat()
    })

@csrf_exempt
def alertas_api(request):
    """API de alertas"""
    alertas = [
        {'id': 1, 'tipo': 'chuva_forte', 'severidade': 'alta', 
         'titulo': 'Chuva Forte', 'mensagem': 'Chuva forte prevista',
         'regiao': 'Zona Norte', 'lat': -22.9333, 'lng': -43.2333},
        {'id': 2, 'tipo': 'alagamento', 'severidade': 'media',
         'titulo': 'Risco de Alagamento', 'mensagem': 'Pontos de alagamento',
         'regiao': 'Zona Sul', 'lat': -22.9711, 'lng': -43.1822}
    ]
    
    return JsonResponse({
        'success': True,
        'alertas': alertas,
        'total': len(alertas),
        'timestamp': datetime.now().isoformat()
    })


# VIDEO MONITORAMENTO
@login_required(login_url='login')
@never_cache
def videomonitoramento(request):
    """Dashboard de Videomonitoramento"""
    return render(request, 'mapa_novo/videomonitoramento.html')

# API DE CAMERAS
@csrf_exempt
def cameras_api_local(request):
    """API de câmeras com fallback para dados locais"""
    import requests
    import csv
    from io import StringIO
    
    try:
        response = requests.get('https://aplicativo.cocr.com.br/cameras_api', timeout=10)
        if response.status_code == 200:
            try:
                # Parsear CSV
                csv_data = response.text
                reader = csv.reader(StringIO(csv_data), delimiter=';')
                
                cameras = []
                for row in reader:
                    if len(row) >= 4:
                        lat, lng, nome, id_cam = row[0], row[1], row[2], row[3]
                        
                        # Determinar tipo baseado no nome
                        is_fixa = nome.upper().endswith('- FIXA')
                        tipo = 'fixa' if is_fixa else 'movel'
                        
                        # Limpar nome (remover "- FIXA" se tiver)
                        nome_limpo = nome.replace(' - FIXA', '').replace(' - fixa', '').strip()
                        
                        cameras.append({
                            'id': id_cam,
                            'nome': nome,  # Nome com "- FIXA" para identificar
                            'nome_limpo': nome_limpo,
                            'lat': float(lat),
                            'lng': float(lng),
                            'tipo': tipo,
                            'fixa': is_fixa,
                            'status': 'Sim',
                            'url_stream': f'https://dev.tixxi.rio/outvideo2/?CODE={id_cam}&KEY=H4281'
                        })
                
                return JsonResponse({
                    'success': True, 
                    'data': cameras, 
                    'count': len(cameras)
                })
                
            except Exception as e:
                logger.warning(f"Erro ao parsear CSV: {e}")
                pass
                
    except Exception as e:
        logger.warning(f"Erro ao buscar câmeras da API externa: {e}")
    
    # Fallback: retornar dados do banco local
    try:
        from aplicativo.models import Cameras
        cameras = Cameras.objects.all()[:50]
        data = [{
            'id': cam.id,
            'nome': cam.nome or f'Câmera {cam.id_c}',
            'bairro': cam.bairro or 'Sem bairro',
            'lat': float(cam.lat) if cam.lat else -22.9068,
            'lng': float(cam.lon) if cam.lon else -43.1729,
            'tipo': 'fixa',  # Assumir todas fixas no fallback
            'fixa': True,
            'status': cam.status or 'ativa',
            'url_stream': f'https://dev.tixxi.rio/outvideo2/?CODE={cam.id_c}&KEY=H4281'
        } for cam in cameras if cam.lat and cam.lon]
        return JsonResponse({'success': True, 'data': data, 'count': len(data)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e), 'data': []}, status=500)

@csrf_exempt
def chuva_api(request):
    pluviometros = [
        {'id': 1, 'nome': 'Alto da Boa Vista', 'lat': -22.9667, 'lng': -43.2833, 
         'chuva_15min': 12.5, 'chuva_1h': 25.3, 'chuva_24h': 45.8},
        {'id': 2, 'nome': 'Tijuca', 'lat': -22.9333, 'lng': -43.2333, 
         'chuva_15min': 8.2, 'chuva_1h': 18.7, 'chuva_24h': 32.4},
    ]
    return JsonResponse({'success': True, 'data': pluviometros, 
        'stats': {'temperatura_media': 25.3, 'umidade_media': 68, 'chuva_24h': 29.1, 'vento_velocidade': 15}})

@csrf_exempt
def alertas_api(request):
    alertas = [{'id': 1, 'tipo': 'chuva_forte', 'titulo': 'Chuva Forte', 
                'mensagem': 'Chuva forte prevista', 'lat': -22.9333, 'lng': -43.2333}]
    return JsonResponse({'success': True, 'alertas': alertas, 'total': 1})


# VIDEO - SEM LOGIN - DEFINITIVO
def video_dashboard(request):
    return render(request, 'mapa_novo/videomonitoramento.html')

def api_cameras_proxy(request):
    import requests
    try:
        r = requests.get('https://aplicativo.cocr.com.br/cameras_api', timeout=10)
        return JsonResponse(r.json(), safe=False)
    except:
        return JsonResponse({'error': 'API offline'}, status=500)
    


@csrf_exempt
def estagio_proxy(request):
    """
    Proxy para API externa de estágio (API retorna só número)
    """
    try:
        logger.info('Buscando estágio da API externa...')
        
        response = requests.get(
            'http://aplicativo.cocr.com.br/estagio_api_app',
            timeout=10
        )
        
        # Verificar se deu erro
        if response.status_code != 200:
            logger.error(f'API retornou status {response.status_code}')
            return JsonResponse({
                'cor': '#10b981',
                'estagio': 'Estágio 1',
                'mensagem': '',
                'mensagem2': '',
                'id': 1,
                'inicio': timezone.now().isoformat(),
                'fallback': True
            })
        
        # API retorna só o número (ex: "1")
        numero_estagio = int(response.text.strip())
        
        # Mapeamento de cores por nível
        cores = {
            1: '#10b981',  # Verde
            2: '#fbbf24',  # Amarelo
            3: '#f97316',  # Laranja
            4: '#ef4444',  # Vermelho
            5: '#dc2626'   # Vermelho escuro
        }
        
        # Construir resposta completa
        data = {
            'cor': cores.get(numero_estagio, '#10b981'),
            'estagio': f'Estágio {numero_estagio}',
            'mensagem': '',
            'mensagem2': '',
            'id': numero_estagio,
            'inicio': timezone.now().isoformat()
        }
        
        logger.info(f'Estágio recebido: {numero_estagio}')
        return JsonResponse(data)
        
    except requests.exceptions.Timeout:
        logger.error('Timeout ao buscar API externa')
        return JsonResponse({
            'cor': '#10b981',
            'estagio': 'Estágio 1',
            'mensagem': 'API temporariamente indisponível',
            'mensagem2': '',
            'id': 1,
            'inicio': timezone.now().isoformat(),
            'fallback': True
        })
        
    except ValueError as e:
        logger.error(f'Erro ao converter número do estágio: {str(e)}')
        return JsonResponse({
            'cor': '#10b981',
            'estagio': 'Estágio 1',
            'mensagem': 'Formato inválido da API',
            'mensagem2': '',
            'id': 1,
            'inicio': timezone.now().isoformat(),
            'fallback': True
        }, status=500)
        
    except Exception as e:
        logger.error(f'Erro ao buscar estágio: {str(e)}')
        return JsonResponse({
            'cor': '#10b981',
            'estagio': 'Estágio 1',
            'mensagem': 'Erro ao buscar estágio',
            'mensagem2': '',
            'id': 1,
            'inicio': timezone.now().isoformat(),
            'fallback': True
        }, status=500)
        
        # Se API retornar erro 500
        if response.status_code != 200:
            logger.error(f'API externa retornou status {response.status_code}')
            # Retornar valores padrão
            return JsonResponse({
                'cor': '#10b981',
                'estagio': 'Estágio 1',
                'mensagem': '',
                'mensagem2': '',
                'id': 1,
                'inicio': '2025-11-09T18:00:00Z',
                'fallback': True  # Indica que é valor padrão
            })
        
        data = response.json()
        logger.info(f'Estágio recebido: {data.get("estagio")}')
        
        return JsonResponse(data)
        
    except requests.exceptions.Timeout:
        logger.error('Timeout ao buscar API externa')
        return JsonResponse({
            'error': 'Timeout',
            'cor': '#10b981',
            'estagio': 'Estágio 1',
            'mensagem': 'API temporariamente indisponível',
            'mensagem2': '',
            'id': 1,
            'inicio': '2025-11-09T18:00:00Z',
            'fallback': True
        })
        
    except Exception as e:
        logger.error(f'Erro ao buscar estágio: {str(e)}')
        return JsonResponse({
            'error': str(e),
            'cor': '#10b981',
            'estagio': 'Estágio 1',
            'mensagem': 'Erro ao buscar estágio',
            'mensagem2': '',
            'id': 1,
            'inicio': '2025-11-09T18:00:00Z',
            'fallback': True
        }, status=500)

# FUNÇÕES DUPLICADAS REMOVIDAS - mobilidade_dashboard_view e meteorologia_dashboard_view
# Já definidas anteriormente no arquivo

def defesa_civil_view(request):
    """Sistema de Defesa Civil"""
    
    # Buscar dados
    sirenes = Sirene.objects.filter(status='ativa').count()
    ocorrencias = Ocorrencia.objects.filter(status='aberta').count()
    alertas = Alerta.objects.filter(
        data_criacao__date=timezone.now().date()
    ).count()
    
    ocorrencias_recentes = Ocorrencia.objects.order_by('-data_criacao')[:10]
    
    context = {
        'system_name': 'Defesa Civil',
        'system_icon': 'shield-fill-exclamation',
        'sirenes_ativas': sirenes,
        'ocorrencias_abertas': ocorrencias,
        'alertas_dia': alertas,
        'ocorrencias': ocorrencias_recentes,
    }
    
    return render(request, 'sistemas/defesa_civil.html', context)




@csrf_exempt
def verificar_status_cameras(request):
    """
    Endpoint para verificar status das câmeras
    GET: Retorna status de todas as câmeras
    POST: Verifica câmera específica
    """
    try:
        # Buscar câmeras da API principal
        response = requests.get('https://aplicativo.cocr.com.br/camera_api_json', timeout=10)
        data = response.json()
        
        cameras_status = []
        
        for cam in data.get('cameras', []):
            camera_id = cam.get('id')
            nome = cam.get('nome', '')
            
            # Verificar se tem URL de stream
            stream_url = cam.get('stream_url') or cam.get('url')
            
            # Lógica de detecção de status
            status = 'online'  # Padrão
            motivo = None
            
            # MÉTODO 1: Verificar timestamp (se existir)
            ultima_atualizacao = cam.get('ultima_atualizacao') or cam.get('last_update')
            if ultima_atualizacao:
                try:
                    # Converter timestamp para datetime
                    last_update = datetime.fromisoformat(ultima_atualizacao.replace('Z', '+00:00'))
                    agora = datetime.now(last_update.tzinfo)
                    
                    # Se não atualizou há mais de 10 minutos, considerar offline
                    if (agora - last_update) > timedelta(minutes=10):
                        status = 'offline'
                        motivo = 'Sem atualização há mais de 10 minutos'
                except:
                    pass
            
            # MÉTODO 2: Verificar se tem stream_url válida
            if not stream_url or stream_url == '':
                status = 'offline'
                motivo = 'URL de stream não configurada'
            
            # MÉTODO 3: Ping na URL (opcional - pode ser lento)
            # Descomentar se quiser ativar:
            # elif stream_url:
            #     try:
            #         head_response = requests.head(stream_url, timeout=3)
            #         if head_response.status_code >= 400:
            #             status = 'offline'
            #             motivo = f'HTTP {head_response.status_code}'
            #     except requests.exceptions.RequestException as e:
            #         status = 'offline'
            #         motivo = 'Stream inacessível'
            
            cameras_status.append({
                'camera_id': camera_id,
                'nome': nome,
                'status': status,
                'motivo': motivo,
                'lat': cam.get('lat'),
                'lon': cam.get('lon'),
                'ultima_verificacao': datetime.now().isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'total': len(cameras_status),
            'online': len([c for c in cameras_status if c['status'] == 'online']),
            'offline': len([c for c in cameras_status if c['status'] == 'offline']),
            'cameras': cameras_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar status das câmeras: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def ping_camera(request):
    """
    Verificar se uma câmera específica está respondendo
    POST: { "camera_id": "004227", "stream_url": "https://..." }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        import json
        body = json.loads(request.body)
        
        camera_id = body.get('camera_id')
        stream_url = body.get('stream_url')
        
        if not stream_url:
            return JsonResponse({
                'camera_id': camera_id,
                'status': 'offline',
                'motivo': 'URL não fornecida'
            })
        
        # Tentar HEAD request na URL do stream
        try:
            response = requests.head(stream_url, timeout=5)
            
            if response.status_code == 200:
                return JsonResponse({
                    'camera_id': camera_id,
                    'status': 'online',
                    'http_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                })
            else:
                return JsonResponse({
                    'camera_id': camera_id,
                    'status': 'offline',
                    'motivo': f'HTTP {response.status_code}',
                    'http_code': response.status_code
                })
                
        except requests.exceptions.Timeout:
            return JsonResponse({
                'camera_id': camera_id,
                'status': 'offline',
                'motivo': 'Timeout'
            })
        except requests.exceptions.ConnectionError:
            return JsonResponse({
                'camera_id': camera_id,
                'status': 'offline',
                'motivo': 'Conexão recusada'
            })
        except Exception as e:
            return JsonResponse({
                'camera_id': camera_id,
                'status': 'offline',
                'motivo': str(e)
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
def camera_stream_info(request, camera_id):
    """Info de stream"""
    return JsonResponse({'camera_id': str(int(camera_id)), 'stream_available': False, 'snapshot_available': True})

@csrf_exempt
def cameras_status(request):
    """Status geral"""
    return JsonResponse({'streaming_enabled': False, 'snapshot_enabled': True})

@csrf_exempt
def camera_hls_placeholder(request, camera_id):
    """Placeholder HLS"""
    return JsonResponse({'error': 'HLS não disponível', 'camera_id': str(int(camera_id))}, status=503)

# ============================================
# CONFIGURAÇÕES DE SNAPSHOT
# ============================================
SNAPSHOT_TIMEOUT = 5
SNAPSHOT_RETRY_ATTEMPTS = 2
CACHE_TTL = 60

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@lru_cache(maxsize=100)
def get_snapshot_urls(camera_id: str) -> list:
    """
    Retorna lista de URLs candidatas para snapshot da câmera.
    URLs são testadas na ordem de prioridade.
    """
    # Normalizar IDs (tentar múltiplos formatos)
    ids_to_try = [camera_id]
    
    if camera_id.isdigit():
        # Tentar formatos: 6, 06, 006, 0006, 00006, 000006
        for width in [2, 3, 4, 5, 6]:
            padded = camera_id.zfill(width)
            if padded not in ids_to_try:
                ids_to_try.append(padded)
        
        # Tentar formato 10XX
        if len(camera_id) <= 4:
            ids_to_try.append(f"10{camera_id.zfill(2)}")
    
    urls = []
    for cam_id in ids_to_try:
        urls.extend([
            # Prioridade 1: API de snapshot dedicada
            f'https://dev.tixxi.rio/outvideo2/snapshot.php?CODE={cam_id}&KEY=H4281',
            f'https://dev.tixxi.rio/outvideo2/snapshot?CODE={cam_id}&KEY=H4281',
            
            # Prioridade 2: Aplicativo principal
            f'https://aplicativo.cocr.com.br/camera/{cam_id}/snapshot.jpg',
            f'https://aplicativo.cocr.com.br/snapshot/{cam_id}.jpg',
            f'https://aplicativo.cocr.com.br/cameras/snapshot/{cam_id}.jpg',
            
            # Prioridade 3: Endpoints alternativos
            f'http://aplicativo.cocr.com.br/camera/{cam_id}/snapshot.jpg',
        ])
    
    return urls


def try_fetch_snapshot(url: str, timeout: int = SNAPSHOT_TIMEOUT) -> tuple:
    """
    Tenta buscar snapshot de uma URL.
    
    Returns:
        tuple: (success: bool, content: bytes, status_code: int, error: str)
    """
    try:
        response = requests.get(url, timeout=timeout, verify=False)
        
        # Validar resposta
        if response.status_code == 200 and len(response.content) > 100:
            # Verificar se é realmente uma imagem
            content_type = response.headers.get('content-type', '').lower()
            if any(t in content_type for t in ['image', 'jpeg', 'jpg', 'png']):
                return (True, response.content, 200, None)
        
        return (False, None, response.status_code, f"Invalid response: {response.status_code}")
        
    except requests.exceptions.Timeout:
        return (False, None, 0, "Timeout")
    except requests.exceptions.ConnectionError:
        return (False, None, 0, "Connection failed")
    except Exception as e:
        return (False, None, 0, str(e)[:100])


def generate_professional_placeholder(camera_id: str, attempts: int = 0) -> str:
    """
    Gera placeholder SVG profissional para câmera offline.
    """
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    return f'''<svg width="640" height="480" xmlns="http://www.w3.org/2000/svg">
        <!-- Background -->
        <rect width="640" height="480" fill="#0f172a"/>
        <rect width="640" height="480" fill="url(#gradient)" opacity="0.1"/>
        
        <!-- Gradient -->
        <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#1e40af;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#7c3aed;stop-opacity:1" />
            </linearGradient>
        </defs>
        
        <!-- Camera Icon -->
        <g transform="translate(320, 180)">
            <circle r="70" fill="#1e293b" opacity="0.5"/>
            <path d="M -40 -20 L -40 20 L 40 20 L 40 -20 L 20 -20 L 20 -30 L -20 -30 L -20 -20 Z" 
                  fill="#334155" stroke="#475569" stroke-width="2"/>
            <circle r="18" fill="#64748b"/>
            <circle r="12" fill="#334155"/>
            <circle cx="20" cy="-10" r="4" fill="#ef4444"/>
        </g>
        
        <!-- Status Badge -->
        <rect x="240" y="270" width="160" height="36" rx="18" fill="#1e293b" opacity="0.8"/>
        <circle cx="265" cy="288" r="6" fill="#ef4444">
            <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/>
        </circle>
        <text x="280" y="293" font-family="system-ui, -apple-system, sans-serif" 
              font-size="14" fill="#e2e8f0" font-weight="500">OFFLINE</text>
        
        <!-- Camera ID -->
        <text x="320" y="330" font-family="system-ui, -apple-system, sans-serif" 
              font-size="16" fill="#94a3b8" text-anchor="middle" font-weight="300">
            Câmera #{camera_id}
        </text>
        
        <!-- Status Message -->
        <text x="320" y="360" font-family="system-ui, -apple-system, sans-serif" 
              font-size="13" fill="#64748b" text-anchor="middle">
            Aguardando conexão com o servidor
        </text>
        
        <!-- Timestamp -->
        <text x="320" y="385" font-family="'Courier New', monospace" 
              font-size="11" fill="#475569" text-anchor="middle">
            {timestamp} • {attempts} tentativa(s)
        </text>
        
        <!-- Footer -->
        <text x="320" y="450" font-family="system-ui, -apple-system, sans-serif" 
              font-size="10" fill="#334155" text-anchor="middle">
            Sistema de Videomonitoramento • COR
        </text>
    </svg>'''


@csrf_exempt
def camera_snapshot(request, camera_id):
    """Retorna player de stream ao invés de snapshot"""
    
    # Formatar ID
    camera_id_padded = camera_id.zfill(6)
    
    # URL do player
    stream_url = f'https://dev.tixxi.rio/outvideo2/?CODE={camera_id_padded}&KEY=H4281'
    
    # Retornar HTML com iframe
    html = f'''
    <html>
    <head>
        <style>
            body {{ margin: 0; overflow: hidden; background: #000; }}
            iframe {{ width: 100%; height: 100vh; border: none; }}
        </style>
    </head>
    <body>
        <iframe src="{stream_url}" allowfullscreen></iframe>
    </body>
    </html>
    '''
    
    return HttpResponse(html, content_type='text/html')

@csrf_exempt
def camera_stream_view(request, camera_id):
    """
    Player de vídeo ao vivo - Abre quando usuário clica na câmera
    """
    # Normalizar ID
    camera_id_padded = camera_id.zfill(6)
    
    # Buscar info da câmera (opcional)
    try:
        from aplicativo.models import Cameras
        camera = Cameras.objects.get(id_c=camera_id_padded)
        nome = camera.nome
        bairro = camera.bairro
    except:
        nome = f"Câmera {camera_id_padded}"
        bairro = ""
    
    # URL do stream
    stream_url = f'https://dev.tixxi.rio/outvideo2/?CODE={camera_id_padded}&KEY=H4281'
    
    # HTML responsivo com design moderno
    html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{nome} - Ao Vivo</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                background: #0f172a;
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}
            .header {{
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                background: linear-gradient(180deg, rgba(0,0,0,0.9) 0%, transparent 100%);
                padding: 20px 30px;
                color: white;
                z-index: 100;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .camera-info {{
                display: flex;
                align-items: center;
                gap: 15px;
            }}
            .live-badge {{
                background: #10b981;
                padding: 6px 14px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 6px;
                box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);
            }}
            .live-dot {{
                width: 8px;
                height: 8px;
                background: white;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; transform: scale(1); }}
                50% {{ opacity: 0.6; transform: scale(0.9); }}
            }}
            .camera-name {{
                font-size: 18px;
                font-weight: 600;
            }}
            .camera-location {{
                font-size: 14px;
                color: #94a3b8;
            }}
            .close-btn {{
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .close-btn:hover {{
                background: rgba(255,255,255,0.2);
                border-color: rgba(255,255,255,0.3);
                transform: translateY(-1px);
            }}
            .player-container {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
            }}
            iframe {{
                width: 100%;
                height: 100%;
                border: none;
            }}
            .loading {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: white;
                font-size: 16px;
                display: none;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="camera-info">
                <div class="live-badge">
                    <div class="live-dot"></div>
                    AO VIVO
                </div>
                <div>
                    <div class="camera-name">{nome}</div>
                    <div class="camera-location">📍 {bairro}</div>
                </div>
            </div>
            <button class="close-btn" onclick="window.close()">
                <span>✕</span>
                <span>Fechar</span>
            </button>
        </div>
        
        <div class="player-container">
            <div class="loading">Carregando transmissão...</div>
            <iframe src="{stream_url}" allowfullscreen></iframe>
        </div>
    </body>
    </html>
    '''
    
    return HttpResponse(html, content_type='text/html')



# ============================================
# LOGIN SEGURO COM PROTEÇÃO
# ============================================
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    """View de login com segurança reforçada"""
    # Se já está autenticado, redirecionar
    if request.user.is_authenticated:
        return redirect('cor_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Validação básica
        if not username or not password:
            messages.error(request, 'Por favor, preencha todos os campos.')
            logger.warning(f'Tentativa de login sem credenciais completas')
            return render(request, 'login.html')
        
        # Limitar tamanho do username (prevenir ataques)
        if len(username) > 150:
            messages.error(request, 'Credenciais inválidas.')
            logger.warning(f'Tentativa de login com username muito longo')
            return render(request, 'login.html')
        
        # Tentar autenticar
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login bem-sucedido
            auth_login(request, user)
            
            # Configurar sessão segura
            request.session.set_expiry(43200)  # 12 horas
            request.session['last_activity'] = str(user.last_login)
            
            # Log de sucesso
            logger.info(f'Login bem-sucedido: {username}')
            messages.success(request, f'Bem-vindo, {user.username}!')
            
            # Redirecionar
            next_url = request.GET.get('next', 'cor_dashboard')
            return redirect(next_url)
        else:
            # Login falhou
            logger.warning(f'Tentativa de login falhou: {username} (IP: {request.META.get("REMOTE_ADDR")})')
            messages.error(request, 'Usuário ou senha inválidos.')
    
    return render(request, 'login.html')

@login_required(login_url='login')
@never_cache
def logout_view(request):
    """View de logout segura"""
    username = request.user.username
    auth_logout(request)
    logger.info(f'Logout: {username}')
    messages.info(request, 'Você saiu do sistema com segurança.')
    return redirect('login')

@login_required(login_url='login')
@never_cache
def dashboard(request):
    """Dashboard principal"""
    return redirect('cor_dashboard')

# ============================================
# APIS COM DADOS DE EXEMPLO PARA O MAPA COR
# ============================================

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse


@api_view(['GET'])
def ventos_api(request):
    """API de ventos com dados de exemplo"""
    dados_exemplo = [
        {
            "id": 1,
            "nome": "Estação Ventos Centro",
            "latitude": -22.9035,
            "longitude": -43.2096,
            "velocidade": 15.5,
            "direcao": "NE",
            "rajada": 22.0
        },
        {
            "id": 2,
            "nome": "Estação Ventos Zona Sul",
            "latitude": -22.9711,
            "longitude": -43.1822,
            "velocidade": 18.2,
            "direcao": "SE",
            "rajada": 25.5
        }
    ]
    return Response({
        'success': True,
        'data': dados_exemplo,
        'count': len(dados_exemplo)
    })


@api_view(['GET'])
def waze_api(request):
    """API do Waze com dados de exemplo"""
    alertas_exemplo = [
        {
            "id": 1,
            "type": "ACCIDENT",
            "latitude": -22.9068,
            "longitude": -43.1729,
            "street": "Av. Rio Branco",
            "city": "Rio de Janeiro",
            "subtype": "ACCIDENT_MINOR",
            "reliability": 8
        },
        {
            "id": 2,
            "type": "JAM",
            "latitude": -22.9133,
            "longitude": -43.2096,
            "street": "Av. Presidente Vargas",
            "city": "Rio de Janeiro",
            "level": 4,
            "speed": 5
        }
    ]
    
    jams_exemplo = [
        {
            "id": 1,
            "level": 3,
            "street": "Av. Brasil",
            "city": "Rio de Janeiro",
            "speed": 10,
            "length": 500,
            "line": [
                {"latitude": -22.8708, "longitude": -43.2772},
                {"latitude": -22.8712, "longitude": -43.2780}
            ]
        }
    ]
    
    return Response({
        'success': True,
        'alerts': alertas_exemplo,
        'jams': jams_exemplo,
        'count': len(alertas_exemplo) + len(jams_exemplo)
    })


@api_view(['GET'])
def pluviometros_view(request):
    """API de pluviômetros com dados de exemplo"""
    dados_exemplo = [
        {
            "id": 1,
            "nome": "Pluviômetro Centro",
            "latitude": -22.9035,
            "longitude": -43.2096,
            "chuva_15min": 2.5,
            "chuva_1h": 8.0,
            "chuva_24h": 25.0,
            "status": "normal"
        },
        {
            "id": 2,
            "nome": "Pluviômetro Tijuca",
            "latitude": -22.9256,
            "longitude": -43.2378,
            "chuva_15min": 5.2,
            "chuva_1h": 15.5,
            "chuva_24h": 45.0,
            "status": "atencao"
        },
        {
            "id": 3,
            "nome": "Pluviômetro Zona Sul",
            "latitude": -22.9711,
            "longitude": -43.1822,
            "chuva_15min": 1.0,
            "chuva_1h": 3.5,
            "chuva_24h": 12.0,
            "status": "normal"
        }
    ]
    return Response({
        'success': True,
        'data': dados_exemplo,
        'count': len(dados_exemplo)
    })


@api_view(['GET'])
def eventos_view(request):
    """API de eventos com dados de exemplo"""
    eventos_exemplo = [
        {
            "id": 1,
            "tipo": "Alagamento",
            "descricao": "Alagamento na Av. Brasil",
            "latitude": -22.8708,
            "longitude": -43.2772,
            "status": "ativo",
            "data_hora": "2025-11-19T17:00:00"
        },
        {
            "id": 2,
            "tipo": "Deslizamento",
            "descricao": "Risco de deslizamento na Rocinha",
            "latitude": -22.9881,
            "longitude": -43.2489,
            "status": "monitoramento",
            "data_hora": "2025-11-19T16:30:00"
        }
    ]
    return Response({
        'success': True,
        'data': eventos_exemplo,
        'count': len(eventos_exemplo)
    })


@api_view(['GET'])
def ocorrencias_view(request):
    """API de ocorrências com dados de exemplo"""
    ocorrencias_exemplo = [
        {
            "id": 1,
            "tipo": "Queda de árvore",
            "endereco": "Rua das Laranjeiras, 340",
            "latitude": -22.9324,
            "longitude": -43.1812,
            "status": "em_atendimento",
            "prioridade": "media",
            "data_hora": "2025-11-19T15:45:00"
        },
        {
            "id": 2,
            "tipo": "Falta de energia",
            "endereco": "Av. Atlântica, 1500",
            "latitude": -22.9711,
            "longitude": -43.1822,
            "status": "pendente",
            "prioridade": "alta",
            "data_hora": "2025-11-19T16:20:00"
        }
    ]
    return Response({
        'success': True,
        'data': ocorrencias_exemplo,
        'count': len(ocorrencias_exemplo)
    })


@api_view(['GET'])
def calor_api(request):
    """API de dados de calor"""
    return Response({
        'success': True,
        'temperatura': 32.5,
        'sensacao_termica': 38.0,
        'umidade': 65,
        'nivel_alerta': 'moderado'
    })


@api_view(['GET'])
def mobilidade_api(request):
    """API de mobilidade"""
    return Response({
        'nivel': 'normal',
        'transito': {
            'nivel': 'normal',
            'descricao': 'Trânsito fluindo normalmente'
        },
        'metro': {
            'status': 'normal',
            'descricao': 'Operação normal em todas as linhas'
        },
        'onibus': {
            'status': 'normal',
            'descricao': 'Frota operando normalmente'
        }
    })

# ============================================
# VIEW DE TESTE - SEM PROTEÇÃO
# ============================================
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def test_api_sem_protecao(request):
    """API de teste sem proteção"""
    return Response({
        'status': 'OK',
        'message': 'API funcionando sem proteção!',
        'user_authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else 'Anônimo'
    })

# ============================================
# APIs DE MOBILIDADE
# ============================================

@api_view(['GET'])
def api_transito_status(request):
    """API de status do trânsito"""
    import datetime
    
    hora_atual = datetime.datetime.now().hour
    
    # Simular status baseado na hora
    if 7 <= hora_atual <= 9 or 17 <= hora_atual <= 19:
        nivel = 3
        descricao = "Trânsito Intenso"
        cor = "#ef4444"
        lentidao = 45
        velocidade = 25
    elif 10 <= hora_atual <= 16:
        nivel = 2
        descricao = "Trânsito Moderado"
        cor = "#f59e0b"
        lentidao = 20
        velocidade = 40
    else:
        nivel = 1
        descricao = "Trânsito Normal"
        cor = "#10b981"
        lentidao = 5
        velocidade = 55
    
    return Response({
        'success': True,
        'data': {
            'nivel': nivel,
            'descricao': descricao,
            'cor': cor,
            'lentidao_km': lentidao,
            'velocidade_media': velocidade,
            'hora': hora_atual
        }
    })


@api_view(['GET'])
def api_brt(request):
    """API de linhas BRT"""
    linhas = [
        {
            'nome': 'TransCarioca',
            'cor': '#0066cc',
            'status': 'Normal',
            'status_code': 'normal',
            'estacoes': 45,
            'extensao': '39 km',
            'tempo_medio': '60 min',
            'intervalo': '8-12 min'
        },
        {
            'nome': 'TransOeste',
            'cor': '#00a651',
            'status': 'Normal',
            'status_code': 'normal',
            'estacoes': 52,
            'extensao': '56 km',
            'tempo_medio': '75 min',
            'intervalo': '10-15 min'
        },
        {
            'nome': 'TransOlímpica',
            'cor': '#f7941e',
            'status': 'Normal',
            'status_code': 'normal',
            'estacoes': 18,
            'extensao': '26 km',
            'tempo_medio': '35 min',
            'intervalo': '5-8 min'
        },
        {
            'nome': 'TransBrasil',
            'cor': '#ed1c24',
            'status': 'Normal',
            'status_code': 'normal',
            'estacoes': 28,
            'extensao': '32 km',
            'tempo_medio': '45 min',
            'intervalo': '7-10 min'
        }
    ]
    
    return Response({
        'success': True,
        'data': linhas,
        'count': len(linhas)
    })


@api_view(['GET'])
def api_metro(request):
    """API de linhas de metrô"""
    linhas = [
        {
            'nome': 'Linha 1 (Laranja)',
            'cor': '#ff6600',
            'status': 'Normal',
            'status_code': 'normal',
            'estacoes': 19,
            'extensao': '20,4 km',
            'intervalo': '4-6 min',
            'origem': 'Ipanema/General Osório',
            'destino': 'Uruguai'
        },
        {
            'nome': 'Linha 2 (Verde)',
            'cor': '#00a651',
            'status': 'Normal',
            'status_code': 'normal',
            'estacoes': 18,
            'extensao': '31,7 km',
            'intervalo': '5-8 min',
            'origem': 'Pavuna',
            'destino': 'Botafogo'
        },
        {
            'nome': 'Linha 4 (Amarela)',
            'cor': '#ffcc00',
            'status': 'Normal',
            'status_code': 'normal',
            'estacoes': 6,
            'extensao': '16 km',
            'intervalo': '6-10 min',
            'origem': 'Ipanema/General Osório',
            'destino': 'Jardim Oceânico'
        }
    ]
    
    return Response({
        'success': True,
        'data': linhas,
        'count': len(linhas)
    })


@api_view(['GET'])
def api_bike_rio(request):
    """API de estações Bike Rio"""
    import random
    
    estacoes = []
    nomes = [
        'Copacabana - Siqueira Campos', 'Ipanema - Praça General Osório',
        'Leblon - Ataulfo de Paiva', 'Botafogo - Voluntários da Pátria',
        'Flamengo - Praia do Flamengo', 'Centro - Praça XV'
    ]
    
    for i, nome in enumerate(nomes):
        bikes = random.randint(0, 15)
        vagas = random.randint(5, 20)
        
        estacoes.append({
            'id': i + 1,
            'nome': nome,
            'bikes_disponiveis': bikes,
            'vagas_disponiveis': vagas,
            'status': 'Operacional' if bikes > 0 else 'Sem Bikes'
        })
    
    total_bikes = sum(e['bikes_disponiveis'] for e in estacoes)
    
    return Response({
        'success': True,
        'data': estacoes,
        'count': len(estacoes),
        'total_bikes': total_bikes
    })


# ============================================
# API CSI - Coeficiente de Severidade de Impacto
# ============================================

@api_view(['GET'])
def api_csi_top5(request):
    """API para obter Top 5 CSI (Coeficiente de Severidade de Impacto)

    Usa sistema de cache para resposta instantanea.
    Os dados sao atualizados em background a cada 5 minutos.
    """
    try:
        from aplicativo.services.csi_api import (
            get_csi_top5_cached,
            get_csi_cache_status,
            start_csi_background_updater
        )

        # Garantir que o atualizador em background esta rodando
        start_csi_background_updater()

        # Obter dados do cache (resposta instantanea)
        data = get_csi_top5_cached()
        cache_status = get_csi_cache_status()

        if data:
            return Response({
                'success': True,
                'data': data,
                'cache': cache_status,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return Response({
                'success': False,
                'error': 'Dados CSI ainda carregando, tente novamente em alguns segundos',
                'cache': cache_status,
                'data': None
            }, status=503)

    except Exception as e:
        logger.error(f"Erro na API CSI: {str(e)}")
        return Response({
            'success': False,
            'error': str(e),
            'data': None
        }, status=500)


@api_view(['POST'])
def api_csi_refresh(request):
    """Forca atualizacao do cache CSI"""
    try:
        from aplicativo.services.csi_api import force_cache_refresh, get_csi_cache_status

        force_cache_refresh()
        cache_status = get_csi_cache_status()

        return Response({
            'success': True,
            'message': 'Atualizacao do cache iniciada',
            'cache': cache_status
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================
# TIXXI API - Cameras, Escolas, Bolsões
# ============================================

import threading
import time

# Cache global para token TIXXI
_tixxi_token_cache = {
    'access_token': None,
    'refresh_token': None,
    'expires_at': None
}
_tixxi_lock = threading.Lock()

TIXXI_CONFIG = {
    'auth_url': 'https://tixxi.rio/tixxi/api/cora/auth.php?action=login',
    'cameras_url': 'https://tixxi.rio/tixxi/api/cora/cameras',
    'schools_url': 'https://tixxi.rio/tixxi/api/cora/schools',
    'inundation_url': 'https://tixxi.rio/tixxi/api/cora/inundation',
    'user': 'cora',
    'pass': 'Cor@2025!'
}


def _get_tixxi_token():
    """Obtém token TIXXI com cache automático"""
    global _tixxi_token_cache

    with _tixxi_lock:
        # Verifica se token ainda é válido (com margem de 60 segundos)
        if (_tixxi_token_cache['access_token'] and
            _tixxi_token_cache['expires_at'] and
            datetime.now() < _tixxi_token_cache['expires_at'] - timedelta(seconds=60)):
            return _tixxi_token_cache['access_token']

        # Busca novo token
        try:
            response = requests.post(
                TIXXI_CONFIG['auth_url'],
                json={"user": TIXXI_CONFIG['user'], "pass": TIXXI_CONFIG['pass']},
                verify=False,
                timeout=10,
                allow_redirects=True
            )

            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    _tixxi_token_cache['access_token'] = data['access_token']
                    _tixxi_token_cache['refresh_token'] = data.get('refresh_token')
                    # Token expira em ~1 hora, guardamos 50 minutos
                    _tixxi_token_cache['expires_at'] = datetime.now() + timedelta(minutes=50)
                    logger.info("TIXXI: Token obtido com sucesso")
                    return data['access_token']

            logger.error(f"TIXXI Auth Error: {response.text}")
            return None

        except Exception as e:
            logger.error(f"TIXXI Auth Exception: {e}")
            return None


def _fetch_tixxi_data(endpoint_url):
    """Busca dados de um endpoint TIXXI"""
    token = _get_tixxi_token()
    if not token:
        return None, "Falha na autenticação TIXXI"

    try:
        response = requests.get(
            endpoint_url,
            headers={'Authorization': f'Bearer {token}'},
            verify=False,
            timeout=30,
            allow_redirects=True
        )

        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 401:
            # Token expirado, limpa cache e tenta novamente
            with _tixxi_lock:
                _tixxi_token_cache['access_token'] = None
            return _fetch_tixxi_data(endpoint_url)  # Retry uma vez
        else:
            return None, f"HTTP {response.status_code}: {response.text}"

    except Exception as e:
        return None, str(e)


@api_view(['GET'])
def api_tixxi_cameras(request):
    """API de câmeras via TIXXI"""
    try:
        data, error = _fetch_tixxi_data(TIXXI_CONFIG['cameras_url'])

        if error:
            return Response({'success': False, 'error': error}, status=500)

        # Filtros opcionais
        zona = request.GET.get('zona', None)
        search = request.GET.get('search', None)

        cameras = []
        for cam in data:
            try:
                lat = float(cam.get('Latitude', 0))
                lng = float(cam.get('Longitude', 0))

                if lat == 0 or lng == 0:
                    continue

                # Filtro por zona
                if zona and zona.lower() not in cam.get('CameraZone', '').lower():
                    continue

                # Filtro por busca
                if search and search.lower() not in cam.get('CameraName', '').lower():
                    continue

                cameras.append({
                    'id': cam.get('CameraCode'),
                    'nome': cam.get('CameraName'),
                    'zona': cam.get('CameraZone'),
                    'bairro': cam.get('CameraLocality'),
                    'lat': lat,
                    'lng': lng,
                    'url': cam.get('URL', '').replace('\\/', '/')
                })
            except:
                continue

        return Response({
            'success': True,
            'data': cameras,
            'count': len(cameras),
            'source': 'TIXXI'
        })

    except Exception as e:
        logger.error(f"api_tixxi_cameras error: {e}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
def api_tixxi_escolas(request):
    """API de escolas via TIXXI"""
    try:
        data, error = _fetch_tixxi_data(TIXXI_CONFIG['schools_url'])

        if error:
            return Response({'success': False, 'error': error}, status=500)

        # Filtros opcionais
        bairro = request.GET.get('bairro', None)
        search = request.GET.get('search', None)

        escolas = []
        for escola in data:
            try:
                # Latitude pode vir com vírgula em vez de ponto
                lat_str = str(escola.get('Latitude', '0')).replace(',', '.')
                lng_str = str(escola.get('Longitude', '0')).replace(',', '.')

                lat = float(lat_str) if lat_str else 0
                lng = float(lng_str) if lng_str else 0

                # Ignora coordenadas inválidas
                if lat == 0 or lng == 0 or abs(lat) > 90 or abs(lng) > 180:
                    continue

                # Corrige longitude duplicada (erro nos dados originais)
                if abs(lng) < 30:  # Longitude de RJ é ~-43
                    continue

                # Filtros
                if bairro and bairro.lower() not in escola.get('Bairro', '').lower():
                    continue

                if search and search.lower() not in escola.get('ItemName', '').lower():
                    continue

                escolas.append({
                    'id': escola.get('ItemID'),
                    'sigla': escola.get('Sigla'),
                    'nome': escola.get('ItemName'),
                    'endereco': escola.get('ItemAddress'),
                    'bairro': escola.get('Bairro'),
                    'cep': escola.get('CEP'),
                    'telefone': escola.get('ItemPhone'),
                    'email': escola.get('ItemMail'),
                    'lat': lat,
                    'lng': lng,
                    'tipo': escola.get('Type', 'Escola'),
                    'ativo': escola.get('Active') == '1'
                })
            except Exception as e:
                continue

        return Response({
            'success': True,
            'data': escolas,
            'count': len(escolas),
            'source': 'TIXXI'
        })

    except Exception as e:
        logger.error(f"api_tixxi_escolas error: {e}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
def api_tixxi_bolsoes(request):
    """API de bolsões de alagamento via TIXXI"""
    try:
        data, error = _fetch_tixxi_data(TIXXI_CONFIG['inundation_url'])

        if error:
            return Response({'success': False, 'error': error}, status=500)

        # Filtros opcionais
        zona = request.GET.get('zona', None)
        bairro = request.GET.get('bairro', None)

        bolsoes = []
        for item in data:
            try:
                lat = float(item.get('Latitude', '0').strip())
                lng = float(item.get('Longitude', '0').strip())

                if lat == 0 or lng == 0:
                    continue

                # Filtros
                if zona and zona.lower() not in item.get('Zona', '').lower():
                    continue

                if bairro and bairro.lower() not in item.get('Bairro', '').lower():
                    continue

                bolsoes.append({
                    'id': item.get('ItemID'),
                    'local': item.get('Local'),
                    'referencia': item.get('Referencia'),
                    'bairro': item.get('Bairro'),
                    'zona': item.get('Zona'),
                    'lat': lat,
                    'lng': lng
                })
            except:
                continue

        return Response({
            'success': True,
            'data': bolsoes,
            'count': len(bolsoes),
            'source': 'TIXXI'
        })

    except Exception as e:
        logger.error(f"api_tixxi_bolsoes error: {e}")
        return Response({'success': False, 'error': str(e)}, status=500)