# -*- coding: utf-8 -*-
"""
Views para Gestao de Eventos
"""
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.decorators.cache import never_cache

from .models import Evento, DataEvento, SecLocaisEvento, Local


# ==================== API DE EVENTOS ====================

@never_cache
def api_eventos_geojson(request):
    """
    Retorna eventos em formato GeoJSON para o mapa

    GET /api/eventos/geojson/
    GET /api/eventos/geojson/?status=Planejado&criticidade=Alta&dias=30
    """
    try:
        # Filtros
        status = request.GET.get('status')
        tipo = request.GET.get('tipo')
        criticidade = request.GET.get('criticidade')
        dias = request.GET.get('dias')
        search = request.GET.get('search')

        queryset = Evento.objects.select_related('endere').prefetch_related('datas', 'seclocaisevento_set')

        if status:
            queryset = queryset.filter(status=status)

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        if criticidade:
            queryset = queryset.filter(criti=criticidade)

        if search:
            queryset = queryset.filter(
                Q(nome_evento__icontains=search) |
                Q(descri__icontains=search)
            )

        # Filtrar por datas proximas
        if dias:
            hoje = datetime.now()
            data_limite = hoje + timedelta(days=int(dias))
            evento_ids = DataEvento.objects.filter(
                data_inicio__gte=hoje,
                data_inicio__lte=data_limite
            ).values_list('evento_id', flat=True).distinct()
            queryset = queryset.filter(id__in=evento_ids)

        features = []

        for evento in queryset:
            # Obter coordenadas do local principal
            lat, lng = None, None
            if evento.endere and evento.endere.location:
                try:
                    coords = evento.endere.location.split(',')
                    lat = float(coords[0].strip())
                    lng = float(coords[1].strip())
                except:
                    pass

            if lat and lng:
                # Cor baseada na criticidade
                cores = {
                    'Alta': '#ff4444',
                    'Média': '#ffaa00',
                    'Normal': '#00cc00',
                    'NA': '#888888',
                }
                cor = cores.get(evento.criti, '#00ffff')

                # Proxima data
                proxima_data = evento.datas.filter(
                    data_inicio__gte=datetime.now()
                ).order_by('data_inicio').first()

                proxima_data_info = None
                if proxima_data:
                    proxima_data_info = {
                        'inicio': proxima_data.data_inicio.isoformat(),
                        'fim': proxima_data.data_fim.isoformat(),
                        'concentracao': proxima_data.data_conce.isoformat() if proxima_data.data_conce else None
                    }

                # Feature principal
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "properties": {
                        "id": evento.id,
                        "nome": evento.nome_evento,
                        "tipo": evento.tipo,
                        "status": evento.status,
                        "criticidade": evento.criti,
                        "cor": cor,
                        "local": evento.endere.local if evento.endere else '',
                        "endereco": evento.endere.end if evento.endere else '',
                        "bairro": evento.endere.bairro if evento.endere else '',
                        "zona": evento.endere.zona if evento.endere else '',
                        "estimativa_publico": evento.qt,
                        "responsavel": evento.respeven,
                        "estrutura": evento.estr,
                        "principal": evento.principal == 'Sim',
                        "raio": evento.raio or 5000,
                        "tem_poligono": evento.tem_poligono,
                        "forma": evento.forma,
                        "proxima_data": proxima_data_info,
                        "pontos_atencao": evento.pontos_atencao,
                    }
                }
                features.append(feature)

                # Adicionar poligono se existir
                if evento.tem_poligono and evento.poligono_coords:
                    try:
                        coords = json.loads(evento.poligono_coords)
                        feature_poligono = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": coords
                            },
                            "properties": {
                                "id": evento.id,
                                "nome": evento.nome_evento,
                                "tipo_feature": "poligono",
                                "cor": cor,
                                "criticidade": evento.criti,
                            }
                        }
                        features.append(feature_poligono)
                    except:
                        pass

                # Adicionar locais secundarios
                for local_sec in evento.seclocaisevento_set.all():
                    if local_sec.location:
                        try:
                            coords_sec = local_sec.location.split(',')
                            lat_sec = float(coords_sec[0].strip())
                            lng_sec = float(coords_sec[1].strip())

                            feature_sec = {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [lng_sec, lat_sec]
                                },
                                "properties": {
                                    "id": evento.id,
                                    "nome": f"{evento.nome_evento} - {local_sec.end}",
                                    "tipo_feature": "local_secundario",
                                    "cor": cor,
                                    "bairro": local_sec.bairro,
                                    "endereco": local_sec.end,
                                }
                            }
                            features.append(feature_sec)
                        except:
                            pass

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        return JsonResponse(geojson)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@never_cache
def api_eventos_lista(request):
    """
    API para listagem de eventos com filtros

    GET /api/eventos/lista/
    """
    try:
        status = request.GET.get('status')
        tipo = request.GET.get('tipo')
        criticidade = request.GET.get('criticidade')
        search = request.GET.get('search')
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))

        queryset = Evento.objects.select_related('endere').prefetch_related('datas')

        if status:
            queryset = queryset.filter(status=status)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if criticidade:
            queryset = queryset.filter(criti=criticidade)
        if search:
            queryset = queryset.filter(
                Q(nome_evento__icontains=search) |
                Q(descri__icontains=search)
            )

        total = queryset.count()
        eventos = queryset.order_by('-id')[offset:offset+limit]

        data = []
        for evento in eventos:
            # Proximas datas
            datas = []
            for d in evento.datas.order_by('data_inicio')[:3]:
                datas.append({
                    'inicio': d.data_inicio.strftime('%d/%m/%Y %H:%M'),
                    'fim': d.data_fim.strftime('%d/%m/%Y %H:%M'),
                })

            data.append({
                'id': evento.id,
                'nome': evento.nome_evento,
                'tipo': evento.tipo,
                'status': evento.status,
                'criticidade': evento.criti,
                'local': evento.endere.local if evento.endere else '',
                'responsavel': evento.respeven,
                'estimativa_publico': evento.qt,
                'principal': evento.principal == 'Sim',
                'datas': datas,
            })

        return JsonResponse({
            'success': True,
            'total': total,
            'count': len(data),
            'data': data
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@never_cache
def api_eventos_timeline(request):
    """
    Retorna eventos organizados em timeline por dia

    GET /api/eventos/timeline/?dias=30
    """
    try:
        dias = int(request.GET.get('dias', 30))
        hoje = datetime.now().date()
        data_limite = hoje + timedelta(days=dias)

        datas = DataEvento.objects.filter(
            data_inicio__date__gte=hoje,
            data_inicio__date__lte=data_limite
        ).select_related('evento', 'evento__endere').order_by('data_inicio')

        timeline = {}
        for data in datas:
            dia = data.data_inicio.date().isoformat()
            if dia not in timeline:
                timeline[dia] = []

            evento = data.evento
            cores = {'Alta': '#ff4444', 'Média': '#ffaa00', 'Normal': '#00cc00'}

            timeline[dia].append({
                'id': evento.id,
                'nome': evento.nome_evento,
                'tipo': evento.tipo,
                'criticidade': evento.criti,
                'cor': cores.get(evento.criti, '#888888'),
                'local': evento.endere.local if evento.endere else '',
                'inicio': data.data_inicio.strftime('%H:%M'),
                'fim': data.data_fim.strftime('%H:%M'),
            })

        return JsonResponse({
            'success': True,
            'timeline': timeline
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@never_cache
def api_eventos_estatisticas(request):
    """
    Retorna estatisticas dos eventos

    GET /api/eventos/estatisticas/
    """
    try:
        total = Evento.objects.count()

        # Por status
        por_status = {}
        for status in ['Planejado', 'Cancelado']:
            por_status[status] = Evento.objects.filter(status=status).count()

        # Por tipo
        por_tipo = {}
        for tipo in Evento.objects.values_list('tipo', flat=True).distinct():
            if tipo:
                por_tipo[tipo] = Evento.objects.filter(tipo=tipo).count()

        # Por criticidade
        por_criticidade = {
            'Normal': Evento.objects.filter(criti='Normal').count(),
            'Média': Evento.objects.filter(criti='Média').count(),
            'Alta': Evento.objects.filter(criti='Alta').count(),
        }

        # Proximos eventos
        hoje = datetime.now()
        proximos_7_dias = DataEvento.objects.filter(
            data_inicio__gte=hoje,
            data_inicio__lte=hoje + timedelta(days=7)
        ).count()

        proximos_30_dias = DataEvento.objects.filter(
            data_inicio__gte=hoje,
            data_inicio__lte=hoje + timedelta(days=30)
        ).count()

        return JsonResponse({
            'success': True,
            'total': total,
            'por_status': por_status,
            'por_tipo': por_tipo,
            'por_criticidade': por_criticidade,
            'proximos_7_dias': proximos_7_dias,
            'proximos_30_dias': proximos_30_dias,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@never_cache
def api_evento_detalhe(request, evento_id):
    """
    Retorna detalhes completos de um evento

    GET /api/eventos/<id>/
    """
    try:
        evento = get_object_or_404(Evento, id=evento_id)

        # Datas
        datas = []
        for d in evento.datas.order_by('data_inicio'):
            datas.append({
                'id': d.id,
                'concentracao': d.data_conce.isoformat() if d.data_conce else None,
                'inicio': d.data_inicio.isoformat(),
                'fim': d.data_fim.isoformat(),
            })

        # Locais secundarios
        locais = []
        for loc in evento.seclocaisevento_set.all():
            coords = None
            if loc.location:
                try:
                    parts = loc.location.split(',')
                    coords = {'lat': float(parts[0]), 'lng': float(parts[1])}
                except:
                    pass
            locais.append({
                'id': loc.id,
                'bairro': loc.bairro,
                'endereco': loc.end,
                'coordenadas': coords,
            })

        # Coordenadas principal
        coords_principal = None
        if evento.endere and evento.endere.location:
            try:
                parts = evento.endere.location.split(',')
                coords_principal = {'lat': float(parts[0]), 'lng': float(parts[1])}
            except:
                pass

        data = {
            'id': evento.id,
            'nome': evento.nome_evento,
            'descricao': evento.descri,
            'tipo': evento.tipo,
            'status': evento.status,
            'criticidade': evento.criti,
            'criticidade_detalhes': {
                'local': evento.local_criti,
                'data': evento.data_criti,
                'hora': evento.hora_criti,
                'mobilidade': evento.mobi_criti,
                'publico': evento.pub_criti,
                'exposicao': evento.exp_criti,
                'figuras_publicas': evento.fp_criti,
                'efetivo': evento.efe_criti,
                'populacao': evento.pop_criti,
                'agravamento': evento.pt_criti,
            },
            'local_principal': {
                'nome': evento.endere.local if evento.endere else '',
                'endereco': evento.endere.end if evento.endere else '',
                'bairro': evento.endere.bairro if evento.endere else '',
                'zona': evento.endere.zona if evento.endere else '',
                'coordenadas': coords_principal,
            },
            'endereco_dispersao': evento.endereco,
            'estrutura': evento.estr,
            'cpe': evento.cpe,
            'estimativa_publico': evento.qt,
            'responsavel': evento.respeven,
            'alinhamento': evento.alinha == 'Sim',
            'forma': evento.forma,
            'principal': evento.principal == 'Sim',
            'pontos_atencao': evento.pontos_atencao,
            'fonte': evento.fonte,
            'raio': evento.raio,
            'tem_poligono': evento.tem_poligono,
            'datas': datas,
            'locais_secundarios': locais,
        }

        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_evento_criar(request):
    """
    Cria um novo evento

    POST /api/eventos/criar/
    """
    try:
        data = json.loads(request.body)

        # Buscar ou criar o local
        local_id = data.get('local_id')
        local = None

        if local_id:
            # Usar local existente
            local = get_object_or_404(Local, id=local_id)
        else:
            # Criar novo local com base no endereco e coordenadas
            endereco_evento = data.get('endereco_evento')
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            if not endereco_evento or not latitude or not longitude:
                return JsonResponse({
                    'success': False,
                    'error': 'Endereco e coordenadas sao obrigatorios quando nao ha local cadastrado'
                }, status=400)

            # Extrair bairro do endereco se possivel
            bairro = None
            endereco_parts = endereco_evento.split(' - ')
            if len(endereco_parts) >= 2:
                # Tentar encontrar bairro valido
                for part in endereco_parts:
                    part_clean = part.strip()
                    # Verificar se e um bairro valido
                    bairros_validos = [b[0] for b in Local.BAIRRO_CHOICE]
                    if part_clean in bairros_validos:
                        bairro = part_clean
                        break

            # Criar o local
            local = Local.objects.create(
                local=data.get('nome_evento', 'Evento')[:250],
                end=endereco_evento[:250],
                location=f"{latitude},{longitude}",
                bairro=bairro
            )

        # Criar evento
        evento = Evento.objects.create(
            nome_evento=data.get('nome_evento'),
            endere=local,
            estr=data.get('estrutura'),
            cpe=data.get('cpe'),
            descri=data.get('descricao'),
            qt=data.get('estimativa_publico'),
            tipo=data.get('tipo'),
            respeven=data.get('responsavel'),
            alinha=data.get('alinhamento', 'Não'),
            local_criti=data.get('criticidade_local', 'Normal'),
            data_criti=data.get('criticidade_data', 'Normal'),
            hora_criti=data.get('criticidade_hora', 'Normal'),
            mobi_criti=data.get('criticidade_mobilidade', 'Normal'),
            pub_criti=data.get('criticidade_publico', 'Normal'),
            exp_criti=data.get('criticidade_exposicao', 'Normal'),
            fp_criti=data.get('criticidade_figuras_publicas', 'Normal'),
            efe_criti=data.get('criticidade_efetivo', 'Normal'),
            pop_criti=data.get('criticidade_populacao', 'Normal'),
            pt_criti=data.get('criticidade_agravamento', 'Normal'),
            principal=data.get('principal', 'Não'),
            status=data.get('status', 'Planejado'),
            forma=data.get('forma'),
            endereco=data.get('endereco_dispersao'),
            raio=data.get('raio', 5000),
            tem_poligono=data.get('tem_poligono', False),
            poligono_coords=json.dumps(data.get('poligono_coords')) if data.get('poligono_coords') else None,
        )

        # Criar datas
        for dt in data.get('datas', []):
            DataEvento.objects.create(
                evento=evento,
                data_conce=datetime.fromisoformat(dt['concentracao']) if dt.get('concentracao') else None,
                data_inicio=datetime.fromisoformat(dt['inicio']),
                data_fim=datetime.fromisoformat(dt['fim']),
            )

        return JsonResponse({
            'success': True,
            'id': evento.id,
            'message': 'Evento criado com sucesso'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT", "PATCH"])
def api_evento_atualizar(request, evento_id):
    """
    Atualiza um evento existente

    PUT /api/eventos/<id>/atualizar/
    """
    try:
        evento = get_object_or_404(Evento, id=evento_id)
        data = json.loads(request.body)

        # Atualizar campos
        if 'nome_evento' in data:
            evento.nome_evento = data['nome_evento']
        if 'descricao' in data:
            evento.descri = data['descricao']
        if 'tipo' in data:
            evento.tipo = data['tipo']
        if 'status' in data:
            evento.status = data['status']
        if 'estrutura' in data:
            evento.estr = data['estrutura']
        if 'estimativa_publico' in data:
            evento.qt = data['estimativa_publico']
        if 'responsavel' in data:
            evento.respeven = data['responsavel']
        if 'forma' in data:
            evento.forma = data['forma']
        if 'principal' in data:
            evento.principal = 'Sim' if data['principal'] else 'Não'

        # Criticidades
        campos_criticidade = [
            ('criticidade_local', 'local_criti'),
            ('criticidade_data', 'data_criti'),
            ('criticidade_hora', 'hora_criti'),
            ('criticidade_mobilidade', 'mobi_criti'),
            ('criticidade_publico', 'pub_criti'),
            ('criticidade_exposicao', 'exp_criti'),
            ('criticidade_figuras_publicas', 'fp_criti'),
            ('criticidade_efetivo', 'efe_criti'),
            ('criticidade_populacao', 'pop_criti'),
            ('criticidade_agravamento', 'pt_criti'),
        ]

        for api_field, model_field in campos_criticidade:
            if api_field in data:
                setattr(evento, model_field, data[api_field])

        evento.save()

        return JsonResponse({
            'success': True,
            'message': 'Evento atualizado com sucesso'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def api_evento_excluir(request, evento_id):
    """
    Exclui um evento

    DELETE /api/eventos/<id>/excluir/
    """
    try:
        evento = get_object_or_404(Evento, id=evento_id)
        evento.delete()

        return JsonResponse({
            'success': True,
            'message': 'Evento excluido com sucesso'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==================== VIEWS DE PAGINAS ====================

@login_required
def eventos_lista_view(request):
    """Pagina de listagem de eventos"""
    eventos = Evento.objects.select_related('endere').prefetch_related('datas').order_by('-id')[:100]

    # Tipos e status para filtros
    tipos = Evento.objects.values_list('tipo', flat=True).distinct()

    context = {
        'eventos': eventos,
        'tipos': [t for t in tipos if t],
        'status_choices': ['Planejado', 'Cancelado'],
        'criticidade_choices': ['Normal', 'Média', 'Alta'],
    }

    return render(request, 'eventos/lista.html', context)


@login_required
def eventos_cadastro_view(request):
    """Pagina de cadastro de evento"""
    locais = Local.objects.all().order_by('local')

    context = {
        'locais': locais,
        'tipos': [t[0] for t in Evento.TIPOEVENTO],
        'responsaveis': [r[0] for r in Evento.RESPEV],
    }

    return render(request, 'eventos/cadastro.html', context)


@login_required
def eventos_editar_view(request, evento_id):
    """Pagina de edicao de evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    locais = Local.objects.all().order_by('local')

    context = {
        'evento': evento,
        'locais': locais,
        'tipos': [t[0] for t in Evento.TIPOEVENTO],
        'responsaveis': [r[0] for r in Evento.RESPEV],
    }

    return render(request, 'eventos/editar.html', context)


@login_required
def eventos_detalhe_view(request, evento_id):
    """Pagina de detalhe de evento"""
    evento = get_object_or_404(
        Evento.objects.select_related('endere').prefetch_related('datas', 'seclocaisevento_set'),
        id=evento_id
    )

    return render(request, 'eventos/detalhe.html', {'evento': evento})


@login_required
def eventos_dashboard_view(request):
    """Dashboard de Eventos com Timeline, Mapa e Planilha"""
    from django.db.models import Min, Max

    # Obter todos os eventos com suas datas
    eventos = Evento.objects.select_related('endere').prefetch_related('datas').order_by('-id')

    # Estatisticas
    total_eventos = eventos.count()
    eventos_planejados = eventos.filter(status='Planejado').count()
    eventos_cancelados = eventos.filter(status='Cancelado').count()

    # Eventos por criticidade
    eventos_alta = eventos.filter(criti='Alta').count()
    eventos_media = eventos.filter(criti='Média').count()
    eventos_normal = eventos.filter(criti='Normal').count()

    # Proximos eventos (proximos 30 dias) + eventos em andamento
    hoje = timezone.now()
    data_limite = hoje + timedelta(days=30)

    # Incluir eventos futuros E eventos em andamento (que ainda nao terminaram)
    proximos_eventos = DataEvento.objects.filter(
        Q(data_inicio__gte=hoje, data_inicio__lte=data_limite) |  # Futuros
        Q(data_inicio__lte=hoje, data_fim__gte=hoje)  # Em andamento
    ).select_related('evento', 'evento__endere').order_by('data_inicio')

    # Eventos acontecendo agora
    eventos_agora = DataEvento.objects.filter(
        data_inicio__lte=hoje,
        data_fim__gte=hoje
    ).select_related('evento', 'evento__endere')

    # Alertas - eventos iniciando nas proximas 2 horas
    duas_horas = hoje + timedelta(hours=2)
    eventos_iniciando = DataEvento.objects.filter(
        data_inicio__gte=hoje,
        data_inicio__lte=duas_horas
    ).select_related('evento', 'evento__endere').order_by('data_inicio')

    # Alertas - eventos terminando nas proximas 2 horas
    eventos_terminando = DataEvento.objects.filter(
        data_fim__gte=hoje,
        data_fim__lte=duas_horas
    ).select_related('evento', 'evento__endere').order_by('data_fim')

    # Tipos para filtro
    tipos = Evento.objects.values_list('tipo', flat=True).distinct()

    context = {
        'eventos': eventos,
        'total_eventos': total_eventos,
        'eventos_planejados': eventos_planejados,
        'eventos_cancelados': eventos_cancelados,
        'eventos_alta': eventos_alta,
        'eventos_media': eventos_media,
        'eventos_normal': eventos_normal,
        'proximos_eventos': proximos_eventos,
        'eventos_agora': eventos_agora,
        'eventos_iniciando': eventos_iniciando,
        'eventos_terminando': eventos_terminando,
        'tipos': [t for t in tipos if t],
    }

    return render(request, 'eventos/dashboard.html', context)


@never_cache
def api_eventos_alertas(request):
    """
    API para obter alertas de eventos em tempo real

    GET /api/eventos/alertas/
    """
    try:
        hoje = timezone.now()
        duas_horas = hoje + timedelta(hours=2)

        alertas = []

        # Eventos iniciando em breve
        eventos_iniciando = DataEvento.objects.filter(
            data_inicio__gte=hoje,
            data_inicio__lte=duas_horas
        ).select_related('evento', 'evento__endere').order_by('data_inicio')

        for de in eventos_iniciando:
            minutos = int((de.data_inicio - hoje).total_seconds() / 60)
            alertas.append({
                'tipo': 'inicio',
                'evento_id': de.evento.id,
                'nome': de.evento.nome_evento,
                'local': de.evento.endere.local if de.evento.endere else '',
                'horario': de.data_inicio.strftime('%H:%M'),
                'minutos_restantes': minutos,
                'criticidade': de.evento.criti,
                'mensagem': f'Inicia em {minutos} minutos'
            })

        # Eventos terminando em breve
        eventos_terminando = DataEvento.objects.filter(
            data_fim__gte=hoje,
            data_fim__lte=duas_horas,
            data_inicio__lte=hoje  # Ja comecou
        ).select_related('evento', 'evento__endere').order_by('data_fim')

        for de in eventos_terminando:
            minutos = int((de.data_fim - hoje).total_seconds() / 60)
            alertas.append({
                'tipo': 'fim',
                'evento_id': de.evento.id,
                'nome': de.evento.nome_evento,
                'local': de.evento.endere.local if de.evento.endere else '',
                'horario': de.data_fim.strftime('%H:%M'),
                'minutos_restantes': minutos,
                'criticidade': de.evento.criti,
                'mensagem': f'Termina em {minutos} minutos'
            })

        # Ordenar por minutos restantes
        alertas.sort(key=lambda x: x['minutos_restantes'])

        return JsonResponse({
            'success': True,
            'alertas': alertas,
            'total': len(alertas)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
