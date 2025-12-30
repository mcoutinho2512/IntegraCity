"""
Views para Sistema de Áreas de Observação
=========================================

Permite desenhar áreas no mapa e inventariar automaticamente
tudo que está dentro (ocorrências, Waze, POIs, etc.)
"""

import json
from datetime import timedelta
from functools import wraps
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import (
    AreaObservacao, InventarioArea, AlertaArea, Cliente, AlertaUsuarioConfirmado
)


def api_login_required(view_func):
    """
    Decorator para APIs que retorna JSON 401 em vez de redirect.
    Isso permite que o JavaScript detecte corretamente quando a sessão expira.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Não autenticado',
                'login_required': True
            }, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


# ============================================
# VIEWS HTML
# ============================================

@login_required
def areas_dashboard(request):
    """Dashboard principal de áreas de observação"""

    cliente = Cliente.objects.filter(ativo=True).first()

    if not cliente:
        return render(request, 'areas/dashboard.html', {
            'erro': 'Nenhum cliente configurado'
        })

    # Buscar áreas ativas
    areas = AreaObservacao.objects.filter(
        cliente=cliente,
        ativa=True
    ).order_by('-criado_em')

    # Contar alertas não lidos por área
    alertas_por_area = {}
    for area in areas:
        count = AlertaArea.objects.filter(
            area=area,
            lido=False
        ).count()
        alertas_por_area[str(area.id)] = count

    context = {
        'cliente': cliente,
        'areas': areas,
        'total_areas': areas.count(),
        'alertas_por_area': alertas_por_area,
        'alertas_json': json.dumps(alertas_por_area),
    }

    return render(request, 'areas/dashboard.html', context)


@login_required
def area_detalhe(request, area_id):
    """Dashboard de uma área específica"""

    area = get_object_or_404(AreaObservacao, id=area_id)

    # Verificar permissão (mesmo cliente)
    cliente = Cliente.objects.filter(ativo=True).first()
    if area.cliente != cliente:
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    # Inventariar
    inventario = area.inventariar()
    nivel = area.calcular_nivel_operacional()

    # Salvar snapshot do inventário
    InventarioArea.objects.create(
        area=area,
        dados=inventario,
        nivel_operacional=nivel
    )

    # Buscar histórico (últimas 24h)
    limite = timezone.now() - timedelta(hours=24)
    historico = InventarioArea.objects.filter(
        area=area,
        data_hora__gte=limite
    ).order_by('-data_hora')[:48]

    # Preparar dados para gráfico
    grafico_data = []
    for inv in reversed(list(historico)):
        grafico_data.append({
            'timestamp': inv.data_hora.strftime('%H:%M'),
            'nivel': inv.nivel_operacional,
            'ocorrencias': inv.dados.get('ocorrencias', {}).get('total', 0),
            'jams': inv.dados.get('waze', {}).get('jams_total', 0),
        })

    # Alertas não lidos
    alertas = AlertaArea.objects.filter(
        area=area,
        lido=False
    ).order_by('-data_hora')[:10]

    # Cores e nomes dos níveis
    niveis_info = {
        1: {'nome': 'Normal', 'cor': '#00ff88'},
        2: {'nome': 'Mobilização', 'cor': '#00D4FF'},
        3: {'nome': 'Atenção', 'cor': '#FFB800'},
        4: {'nome': 'Alerta', 'cor': '#FF6B00'},
        5: {'nome': 'Crise', 'cor': '#FF0055'},
    }

    context = {
        'area': area,
        'inventario': inventario,
        'nivel': nivel,
        'nivel_nome': niveis_info[nivel]['nome'],
        'nivel_cor': niveis_info[nivel]['cor'],
        'grafico_data': json.dumps(grafico_data),
        'alertas': alertas,
        'agora': timezone.now(),
        'geojson': json.dumps(area.geojson),
    }

    return render(request, 'areas/detalhe.html', context)


# ============================================
# APIS JSON
# ============================================

@login_required
def api_listar_areas(request):
    """API para listar todas as áreas"""

    cliente = Cliente.objects.filter(ativo=True).first()

    if not cliente:
        return JsonResponse({'success': False, 'error': 'Cliente não configurado'})

    areas = AreaObservacao.objects.filter(
        cliente=cliente,
        ativa=True
    ).order_by('-criado_em')

    data = []
    for area in areas:
        # Buscar último inventário
        ultimo_inv = area.inventarios.order_by('-data_hora').first()

        data.append({
            'id': str(area.id),
            'nome': area.nome,
            'descricao': area.descricao,
            'cor': area.cor,
            'geojson': area.geojson,
            'criado_em': area.criado_em.isoformat(),
            'ultimo_inventario': ultimo_inv.dados if ultimo_inv else {},
            'nivel_operacional': ultimo_inv.nivel_operacional if ultimo_inv else 1,
            'alertas_nao_lidos': area.alertas.filter(lido=False).count(),
        })

    return JsonResponse({
        'success': True,
        'areas': data,
        'total': len(data)
    })


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_criar_area(request):
    """API para criar nova área de observação"""

    try:
        cliente = Cliente.objects.filter(ativo=True).first()

        if not cliente:
            return JsonResponse({'success': False, 'error': 'Cliente não configurado'}, status=400)

        data = json.loads(request.body)

        # Validar campos obrigatórios
        if not data.get('nome'):
            return JsonResponse({'success': False, 'error': 'Nome é obrigatório'}, status=400)

        if not data.get('geojson'):
            return JsonResponse({'success': False, 'error': 'GeoJSON é obrigatório'}, status=400)

        # Criar área
        area = AreaObservacao.objects.create(
            cliente=cliente,
            criado_por=request.user,
            nome=data.get('nome', 'Área sem nome'),
            descricao=data.get('descricao', ''),
            cor=data.get('cor', '#00D4FF'),
            geojson=data.get('geojson'),
            tipo_desenho=data.get('tipo', 'polygon'),
            ativa=True,
        )

        # Fazer inventário inicial
        inventario = area.inventariar()
        nivel = area.calcular_nivel_operacional()

        # Salvar snapshot
        InventarioArea.objects.create(
            area=area,
            dados=inventario,
            nivel_operacional=nivel
        )

        return JsonResponse({
            'success': True,
            'area_id': str(area.id),
            'nome': area.nome,
            'inventario': inventario,
            'nivel': nivel,
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def api_atualizar_area(request, area_id):
    """API para atualizar uma área existente"""

    try:
        area = get_object_or_404(AreaObservacao, id=area_id)

        # Verificar permissão
        cliente = Cliente.objects.filter(ativo=True).first()
        if area.cliente != cliente:
            return JsonResponse({'error': 'Acesso negado'}, status=403)

        data = json.loads(request.body)

        # Atualizar campos
        if 'nome' in data:
            area.nome = data['nome']
        if 'descricao' in data:
            area.descricao = data['descricao']
        if 'cor' in data:
            area.cor = data['cor']
        if 'geojson' in data:
            area.geojson = data['geojson']
        if 'ativa' in data:
            area.ativa = data['ativa']
        if 'alerta_habilitado' in data:
            area.alerta_habilitado = data['alerta_habilitado']

        # Campos de evento
        if 'evento_nome' in data:
            area.evento_nome = data['evento_nome']
        if 'evento_inicio' in data:
            area.evento_inicio = data['evento_inicio']
        if 'evento_fim' in data:
            area.evento_fim = data['evento_fim']
        if 'plano_contingencia' in data:
            area.plano_contingencia = data['plano_contingencia']

        area.save()

        return JsonResponse({
            'success': True,
            'area_id': str(area.id),
            'nome': area.nome,
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def api_deletar_area(request, area_id):
    """API para deletar (desativar) uma área"""

    try:
        area = get_object_or_404(AreaObservacao, id=area_id)

        # Verificar permissão
        cliente = Cliente.objects.filter(ativo=True).first()
        if area.cliente != cliente:
            return JsonResponse({'error': 'Acesso negado'}, status=403)

        # Soft delete - apenas desativar
        area.ativa = False
        area.save()

        return JsonResponse({
            'success': True,
            'message': f'Área "{area.nome}" desativada com sucesso'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_inventariar_area(request, area_id):
    """API para inventariar área (atualização em tempo real)"""

    try:
        area = get_object_or_404(AreaObservacao, id=area_id)

        # Verificar permissão
        cliente = Cliente.objects.filter(ativo=True).first()
        if area.cliente != cliente:
            return JsonResponse({'error': 'Acesso negado'}, status=403)

        # Inventariar
        inventario = area.inventariar()
        nivel = area.calcular_nivel_operacional()

        # Salvar snapshot
        InventarioArea.objects.create(
            area=area,
            dados=inventario,
            nivel_operacional=nivel
        )

        # Verificar se precisa gerar alertas
        verificar_e_gerar_alertas(area, inventario, nivel)

        # Cores e nomes dos níveis
        niveis_info = {
            1: {'nome': 'Normal', 'cor': '#00ff88'},
            2: {'nome': 'Mobilização', 'cor': '#00D4FF'},
            3: {'nome': 'Atenção', 'cor': '#FFB800'},
            4: {'nome': 'Alerta', 'cor': '#FF6B00'},
            5: {'nome': 'Crise', 'cor': '#FF0055'},
        }

        return JsonResponse({
            'success': True,
            'inventario': inventario,
            'nivel': nivel,
            'nivel_nome': niveis_info[nivel]['nome'],
            'nivel_cor': niveis_info[nivel]['cor'],
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_alertas_area(request, area_id):
    """API para listar alertas de uma área"""

    try:
        area = get_object_or_404(AreaObservacao, id=area_id)

        # Verificar permissão
        cliente = Cliente.objects.filter(ativo=True).first()
        if area.cliente != cliente:
            return JsonResponse({'error': 'Acesso negado'}, status=403)

        alertas = AlertaArea.objects.filter(area=area).order_by('-data_hora')[:50]

        data = [{
            'id': str(a.id),
            'tipo': a.tipo,
            'titulo': a.titulo,
            'descricao': a.descricao,
            'gravidade': a.gravidade,
            'lido': a.lido,
            'data_hora': a.data_hora.isoformat(),
        } for a in alertas]

        return JsonResponse({
            'success': True,
            'alertas': data,
            'total': len(data),
            'nao_lidos': AlertaArea.objects.filter(area=area, lido=False).count()
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_marcar_alerta_lido(request, alerta_id):
    """API para marcar alerta como lido"""

    try:
        alerta = get_object_or_404(AlertaArea, id=alerta_id)
        alerta.lido = True
        alerta.save()

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================
# EXPORTAÇÃO
# ============================================

@login_required
def api_exportar_geojson(request, area_id):
    """Exportar área em formato GeoJSON"""

    area = get_object_or_404(AreaObservacao, id=area_id)

    geojson = {
        "type": "Feature",
        "properties": {
            "nome": area.nome,
            "descricao": area.descricao,
            "cor": area.cor,
            "criado_em": area.criado_em.isoformat(),
            "cliente": area.cliente.nome,
        },
        "geometry": area.geojson.get('geometry', area.geojson)
    }

    response = HttpResponse(
        json.dumps(geojson, indent=2, ensure_ascii=False),
        content_type='application/geo+json'
    )
    response['Content-Disposition'] = f'attachment; filename="area_{area.nome.replace(" ", "_")}.geojson"'

    return response


@login_required
def api_exportar_kml(request, area_id):
    """Exportar área em formato KML (Google Earth)"""

    area = get_object_or_404(AreaObservacao, id=area_id)

    # Extrair coordenadas
    coords = area.geojson.get('geometry', area.geojson).get('coordinates', [[]])[0]
    coords_str = ' '.join([f"{c[0]},{c[1]},0" for c in coords])

    kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{area.nome}</name>
    <description>{area.descricao or ''}</description>
    <Style id="areaStyle">
      <LineStyle>
        <color>ff{area.cor[5:7]}{area.cor[3:5]}{area.cor[1:3]}</color>
        <width>2</width>
      </LineStyle>
      <PolyStyle>
        <color>40{area.cor[5:7]}{area.cor[3:5]}{area.cor[1:3]}</color>
      </PolyStyle>
    </Style>
    <Placemark>
      <name>{area.nome}</name>
      <styleUrl>#areaStyle</styleUrl>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>{coords_str}</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>'''

    response = HttpResponse(kml, content_type='application/vnd.google-earth.kml+xml')
    response['Content-Disposition'] = f'attachment; filename="area_{area.nome.replace(" ", "_")}.kml"'

    return response


@login_required
def api_exportar_relatorio_pdf(request, area_id):
    """Exportar relatório em PDF"""

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
    except ImportError:
        return JsonResponse({
            'success': False,
            'error': 'Biblioteca reportlab não instalada. Execute: pip install reportlab'
        }, status=500)

    area = get_object_or_404(AreaObservacao, id=area_id)
    inventario = area.inventariar()
    nivel = area.calcular_nivel_operacional()

    niveis_info = {
        1: 'E1 - Normal',
        2: 'E2 - Mobilização',
        3: 'E3 - Atenção',
        4: 'E4 - Alerta',
        5: 'E5 - Crise',
    }

    # Criar PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    p.setFont("Helvetica-Bold", 20)
    p.drawString(30, height - 50, "INTEGRACITY - ÁREA DE OBSERVAÇÃO")

    p.setFont("Helvetica-Bold", 14)
    p.drawString(30, height - 80, f"Área: {area.nome}")

    p.setFont("Helvetica", 11)
    p.drawString(30, height - 100, f"Gerado em: {timezone.now().strftime('%d/%m/%Y às %H:%M')}")
    p.drawString(30, height - 115, f"Responsável: {request.user.get_full_name() or request.user.username}")
    p.drawString(30, height - 130, f"Cliente: {area.cliente.nome}")

    # Linha separadora
    p.setStrokeColor(colors.HexColor('#00D4FF'))
    p.line(30, height - 145, width - 30, height - 145)

    # Nível Operacional
    y = height - 175
    p.setFont("Helvetica-Bold", 14)
    p.drawString(30, y, f"NÍVEL OPERACIONAL: {niveis_info[nivel]}")

    # Inventário
    y -= 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(30, y, "INVENTÁRIO DA ÁREA")

    y -= 25
    p.setFont("Helvetica", 11)

    # Ocorrências
    oc = inventario.get('ocorrencias', {})
    p.drawString(40, y, f"• Ocorrências ativas: {oc.get('total', 0)}")
    y -= 18
    p.drawString(55, y, f"- Graves: {oc.get('graves', 0)}")
    y -= 15
    p.drawString(55, y, f"- Moderadas: {oc.get('moderadas', 0)}")
    y -= 15
    p.drawString(55, y, f"- Leves: {oc.get('leves', 0)}")

    y -= 25
    # Waze
    waze = inventario.get('waze', {})
    p.drawString(40, y, f"• Congestionamentos (Waze): {waze.get('jams_total', 0)}")
    y -= 18
    p.drawString(55, y, f"- Severos (nível 4-5): {waze.get('jams_severos', 0)}")
    y -= 15
    p.drawString(55, y, f"- Acidentes: {waze.get('acidentes', 0)}")
    y -= 15
    p.drawString(55, y, f"- Interdições: {waze.get('interdicoes', 0)}")

    y -= 25
    # POIs
    p.drawString(40, y, f"• Escolas: {inventario.get('escolas', 0)}")
    y -= 18
    sirenes = inventario.get('sirenes', {})
    p.drawString(40, y, f"• Sirenes: {sirenes.get('total', 0)} (acionadas: {sirenes.get('acionadas', 0)})")
    y -= 18
    p.drawString(40, y, f"• Câmeras: {inventario.get('cameras', 0)}")

    # Descrição da área
    if area.descricao:
        y -= 35
        p.setFont("Helvetica-Bold", 12)
        p.drawString(30, y, "DESCRIÇÃO")
        y -= 20
        p.setFont("Helvetica", 10)
        # Quebrar texto em linhas
        for linha in area.descricao.split('\n')[:5]:
            p.drawString(40, y, linha[:80])
            y -= 15

    # Evento (se houver)
    if area.evento_nome:
        y -= 25
        p.setFont("Helvetica-Bold", 12)
        p.drawString(30, y, "EVENTO VINCULADO")
        y -= 20
        p.setFont("Helvetica", 11)
        p.drawString(40, y, f"Nome: {area.evento_nome}")
        if area.evento_inicio:
            y -= 18
            p.drawString(40, y, f"Início: {area.evento_inicio.strftime('%d/%m/%Y %H:%M')}")
        if area.evento_fim:
            y -= 18
            p.drawString(40, y, f"Fim: {area.evento_fim.strftime('%d/%m/%Y %H:%M')}")

    # Rodapé
    p.setFont("Helvetica", 8)
    p.setFillColor(colors.gray)
    p.drawString(30, 30, "IntegraCity - Sistema de Gestão de Crises Urbanas")
    p.drawString(width - 150, 30, f"Página 1 de 1")

    # Finalizar
    p.showPage()
    p.save()

    # Retornar PDF
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"relatorio_area_{area.nome.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


# ============================================
# APIs DE ALERTAS CONFIRMADOS PELO USUÁRIO
# ============================================

@api_login_required
@require_http_methods(["GET"])
def api_alertas_confirmados_listar(request):
    """Lista todos os alertas confirmados pelo usuário logado.

    Usado para sincronizar o estado de alertas no navegador
    (resolve problema de perda de dados em modo InPrivate).
    """
    try:
        confirmados = AlertaUsuarioConfirmado.objects.filter(
            usuario=request.user
        ).values_list('alerta_id', flat=True)

        return JsonResponse({
            'success': True,
            'alertas_confirmados': list(confirmados),
            'total': len(confirmados),
            'usuario': request.user.username
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@api_login_required
@require_http_methods(["POST"])
def api_alertas_confirmados_salvar(request):
    """Salva um alerta como confirmado/dispensado pelo usuário.

    Espera JSON com:
    - alerta_id: ID do alerta (string)
    - area_id: ID da área (opcional, UUID)
    - tipo: 'confirmado' ou 'dispensado' (opcional, default 'confirmado')
    """
    try:
        data = json.loads(request.body)

        alerta_id = data.get('alerta_id')
        if not alerta_id:
            return JsonResponse({
                'success': False,
                'error': 'alerta_id é obrigatório'
            }, status=400)

        # Normalizar o ID (remover hifens, lowercase)
        alerta_id_normalizado = str(alerta_id).lower().replace('-', '')

        # Buscar área se fornecida
        area = None
        area_id = data.get('area_id')
        if area_id:
            try:
                area = AreaObservacao.objects.get(id=area_id)
            except AreaObservacao.DoesNotExist:
                pass

        tipo = data.get('tipo', 'confirmado')
        if tipo not in ['confirmado', 'dispensado']:
            tipo = 'confirmado'

        # Criar ou atualizar registro
        confirmacao, created = AlertaUsuarioConfirmado.objects.update_or_create(
            usuario=request.user,
            alerta_id=alerta_id_normalizado,
            defaults={
                'area': area,
                'tipo': tipo,
            }
        )

        return JsonResponse({
            'success': True,
            'created': created,
            'alerta_id': alerta_id_normalizado,
            'tipo': tipo
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@api_login_required
@require_http_methods(["POST"])
def api_alertas_confirmados_salvar_lote(request):
    """Salva múltiplos alertas como confirmados de uma vez.

    Espera JSON com:
    - alertas: lista de IDs de alertas
    """
    try:
        data = json.loads(request.body)

        alertas = data.get('alertas', [])
        if not alertas:
            return JsonResponse({
                'success': False,
                'error': 'Lista de alertas é obrigatória'
            }, status=400)

        salvos = 0
        for alerta_id in alertas:
            alerta_id_normalizado = str(alerta_id).lower().replace('-', '')

            _, created = AlertaUsuarioConfirmado.objects.get_or_create(
                usuario=request.user,
                alerta_id=alerta_id_normalizado,
                defaults={'tipo': 'confirmado'}
            )
            if created:
                salvos += 1

        return JsonResponse({
            'success': True,
            'salvos': salvos,
            'total_enviados': len(alertas)
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def verificar_e_gerar_alertas(area, inventario, nivel_atual):
    """Verifica condições e gera alertas se necessário"""

    if not area.alerta_habilitado:
        return

    # Buscar último inventário para comparar
    ultimo_inv = area.inventarios.order_by('-data_hora').first()
    nivel_anterior = ultimo_inv.nivel_operacional if ultimo_inv else 1

    # Verificar mudança de nível
    if nivel_atual > nivel_anterior:
        AlertaArea.objects.create(
            area=area,
            tipo='nivel_mudou',
            titulo=f'Nível subiu para E{nivel_atual}',
            descricao=f'O nível operacional da área "{area.nome}" subiu de E{nivel_anterior} para E{nivel_atual}.',
            gravidade='critico' if nivel_atual >= 4 else 'atencao'
        )

    # Verificar ocorrências graves
    ocorrencias_graves = inventario.get('ocorrencias', {}).get('graves', 0)
    if ocorrencias_graves >= 3:
        # Verificar se já não tem alerta recente
        alerta_recente = AlertaArea.objects.filter(
            area=area,
            tipo='ocorrencia_grave',
            data_hora__gte=timezone.now() - timedelta(minutes=30)
        ).exists()

        if not alerta_recente:
            AlertaArea.objects.create(
                area=area,
                tipo='ocorrencia_grave',
                titulo=f'{ocorrencias_graves} ocorrências graves na área',
                descricao=f'A área "{area.nome}" possui {ocorrencias_graves} ocorrências com prioridade alta/urgente/crítica.',
                gravidade='critico'
            )

    # Verificar congestionamentos severos
    jams_severos = inventario.get('waze', {}).get('jams_severos', 0)
    if jams_severos >= 5:
        alerta_recente = AlertaArea.objects.filter(
            area=area,
            tipo='jam_severo',
            data_hora__gte=timezone.now() - timedelta(minutes=30)
        ).exists()

        if not alerta_recente:
            AlertaArea.objects.create(
                area=area,
                tipo='jam_severo',
                titulo=f'{jams_severos} congestionamentos severos',
                descricao=f'A área "{area.nome}" possui {jams_severos} congestionamentos de nível 4-5.',
                gravidade='atencao'
            )

    # Verificar sirenes acionadas
    sirenes_acionadas = inventario.get('sirenes', {}).get('acionadas', 0)
    if sirenes_acionadas >= 1:
        alerta_recente = AlertaArea.objects.filter(
            area=area,
            tipo='sirene_acionada',
            data_hora__gte=timezone.now() - timedelta(minutes=60)
        ).exists()

        if not alerta_recente:
            AlertaArea.objects.create(
                area=area,
                tipo='sirene_acionada',
                titulo=f'Sirene acionada na área!',
                descricao=f'{sirenes_acionadas} sirene(s) acionada(s) na área "{area.nome}".',
                gravidade='critico'
            )
