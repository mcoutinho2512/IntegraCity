"""
Views para Sistema de Áreas de Observação
=========================================

Permite desenhar áreas no mapa e inventariar automaticamente
tudo que está dentro (ocorrências, Waze, POIs, etc.)
"""

import json
import zipfile
import tempfile
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
    from django.utils import timezone

    cliente = Cliente.objects.filter(ativo=True).first()

    if not cliente:
        return JsonResponse({'success': False, 'error': 'Cliente não configurado'})

    # Parâmetro para incluir todas as áreas (mesmo inativas)
    incluir_inativas = request.GET.get('incluir_inativas', 'false').lower() == 'true'

    if incluir_inativas:
        areas = AreaObservacao.objects.filter(cliente=cliente).order_by('-criado_em')
    else:
        areas = AreaObservacao.objects.filter(
            cliente=cliente,
            ativa=True
        ).order_by('-criado_em')

    data = []
    agora = timezone.now()

    for area in areas:
        # Verificar se área temporária está dentro do período de exibição
        if area.temporaria:
            # Se tem evento_inicio e ainda não começou, pular
            if area.evento_inicio and area.evento_inicio > agora:
                continue
            # Se tem evento_fim e já passou, pular
            if area.evento_fim and area.evento_fim < agora:
                continue

        # Buscar último inventário
        ultimo_inv = area.inventarios.order_by('-data_hora').first()

        data.append({
            'id': str(area.id),
            'nome': area.nome,
            'descricao': area.descricao,
            'cor': area.cor,
            'tipo_desenho': area.tipo_desenho,
            'geojson': area.geojson,
            'criado_em': area.criado_em.isoformat(),
            'ultimo_inventario': ultimo_inv.dados if ultimo_inv else {},
            'nivel_operacional': ultimo_inv.nivel_operacional if ultimo_inv else 1,
            'alertas_nao_lidos': area.alertas.filter(lido=False).count(),
            # Novos campos
            'temporaria': area.temporaria,
            'importada_de_kml': area.importada_de_kml,
            'grupo_importacao': area.grupo_importacao,
            'arquivo_origem': area.arquivo_origem,
            'evento_inicio': area.evento_inicio.isoformat() if area.evento_inicio else None,
            'evento_fim': area.evento_fim.isoformat() if area.evento_fim else None,
            'ativa': area.ativa,
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
# IMPORTAÇÃO KML/KMZ
# ============================================

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_importar_kml(request):
    """API para importar arquivo KML ou KMZ e criar áreas de observação.

    Suporta:
    - KML: arquivo XML direto
    - KMZ: arquivo ZIP contendo KML

    Tipos de geometria suportados:
    - Polygon → AreaObservacao tipo "polygon"
    - Point → AreaObservacao tipo "marker"
    - LineString → AreaObservacao tipo "polyline"
    """
    try:
        from lxml import etree
    except ImportError:
        return JsonResponse({
            'success': False,
            'error': 'Biblioteca lxml não instalada. Execute: pip install lxml'
        }, status=500)

    try:
        cliente = Cliente.objects.filter(ativo=True).first()
        if not cliente:
            return JsonResponse({'success': False, 'error': 'Cliente não configurado'}, status=400)

        # Verificar se arquivo foi enviado
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'Nenhum arquivo enviado'}, status=400)

        uploaded_file = request.FILES['file']
        filename = uploaded_file.name.lower()

        # Obter prefixo opcional para nomes das áreas
        prefixo = request.POST.get('prefixo', '')
        cor_padrao = request.POST.get('cor', '#00D4FF')

        # Parâmetros de agendamento
        temporaria = request.POST.get('temporaria', 'false').lower() == 'true'
        evento_inicio = request.POST.get('evento_inicio', None)
        evento_fim = request.POST.get('evento_fim', None)

        # Converter datas se fornecidas
        from django.utils import timezone
        from datetime import datetime
        import uuid as uuid_module

        if evento_inicio:
            try:
                evento_inicio = datetime.fromisoformat(evento_inicio.replace('Z', '+00:00'))
                if timezone.is_naive(evento_inicio):
                    evento_inicio = timezone.make_aware(evento_inicio)
            except (ValueError, TypeError):
                evento_inicio = None

        if evento_fim:
            try:
                evento_fim = datetime.fromisoformat(evento_fim.replace('Z', '+00:00'))
                if timezone.is_naive(evento_fim):
                    evento_fim = timezone.make_aware(evento_fim)
            except (ValueError, TypeError):
                evento_fim = None

        # Gerar ID único para agrupar áreas desta importação
        grupo_importacao = str(uuid_module.uuid4())[:8]

        # Processar arquivo
        if filename.endswith('.kmz'):
            # KMZ é um ZIP com KML dentro
            kml_content = extrair_kml_de_kmz(uploaded_file)
        elif filename.endswith('.kml'):
            kml_content = uploaded_file.read()
        else:
            return JsonResponse({
                'success': False,
                'error': 'Formato não suportado. Use arquivos .kml ou .kmz'
            }, status=400)

        if not kml_content:
            return JsonResponse({
                'success': False,
                'error': 'Não foi possível extrair conteúdo KML do arquivo'
            }, status=400)

        # Parse do KML
        placemarks = parse_kml(kml_content)

        if not placemarks:
            return JsonResponse({
                'success': False,
                'error': 'Nenhum elemento geográfico encontrado no arquivo KML'
            }, status=400)

        # Criar áreas para cada placemark
        areas_criadas = []
        erros = []

        for idx, placemark in enumerate(placemarks):
            try:
                nome = placemark.get('name', f'Área Importada {idx + 1}')
                if prefixo:
                    nome = f"{prefixo} - {nome}"

                descricao = placemark.get('description', '')
                geometry = placemark.get('geometry', {})
                tipo = placemark.get('type', 'polygon')
                # Sempre usar a cor selecionada pelo usuário (ignora cor do KML)
                cor = cor_padrao

                # Criar área
                area = AreaObservacao.objects.create(
                    cliente=cliente,
                    criado_por=request.user,
                    nome=nome[:200],
                    descricao=descricao[:1000] if descricao else f'Importado de {uploaded_file.name}',
                    cor=cor,
                    geojson=geometry,
                    tipo_desenho=tipo,
                    ativa=True,
                    # Novos campos de agendamento
                    temporaria=temporaria,
                    importada_de_kml=True,
                    arquivo_origem=uploaded_file.name[:255],
                    grupo_importacao=grupo_importacao,
                    evento_inicio=evento_inicio,
                    evento_fim=evento_fim,
                )

                # Fazer inventário inicial
                inventario = area.inventariar()
                nivel = area.calcular_nivel_operacional()

                InventarioArea.objects.create(
                    area=area,
                    dados=inventario,
                    nivel_operacional=nivel
                )

                areas_criadas.append({
                    'id': str(area.id),
                    'nome': area.nome,
                    'tipo': tipo,
                    'nivel': nivel,
                })

            except Exception as e:
                erros.append(f"Erro ao criar '{nome}': {str(e)}")

        return JsonResponse({
            'success': True,
            'areas_criadas': areas_criadas,
            'total': len(areas_criadas),
            'erros': erros if erros else None,
            'arquivo': uploaded_file.name,
            'grupo_importacao': grupo_importacao,
            'temporaria': temporaria,
            'evento_inicio': evento_inicio.isoformat() if evento_inicio else None,
            'evento_fim': evento_fim.isoformat() if evento_fim else None,
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao processar arquivo: {str(e)}'
        }, status=500)


def extrair_kml_de_kmz(kmz_file):
    """Extrai conteúdo KML de arquivo KMZ (ZIP)"""
    try:
        with zipfile.ZipFile(BytesIO(kmz_file.read()), 'r') as zf:
            # Procurar arquivo .kml dentro do ZIP
            for name in zf.namelist():
                if name.lower().endswith('.kml'):
                    return zf.read(name)

            # Se não encontrou .kml, tentar doc.kml (padrão)
            if 'doc.kml' in zf.namelist():
                return zf.read('doc.kml')

        return None
    except Exception:
        return None


def parse_kml(kml_content):
    """Parse KML e extrai todos os Placemarks com suas geometrias.

    Retorna lista de dicts com:
    - name: nome do placemark
    - description: descrição
    - geometry: GeoJSON da geometria
    - type: tipo (polygon, marker, polyline)
    - color: cor extraída do estilo (se houver)
    """
    from lxml import etree

    try:
        # Converter para bytes se for string (necessário para XML com encoding declaration)
        if isinstance(kml_content, str):
            kml_content = kml_content.encode('utf-8')

        # Parse XML
        root = etree.fromstring(kml_content)

        # Namespace KML
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}

        # Tentar sem namespace se não funcionar
        if root.find('.//kml:Placemark', ns) is None:
            ns = {}
            placemarks = root.findall('.//*[local-name()="Placemark"]')
        else:
            placemarks = root.findall('.//kml:Placemark', ns)

        # Extrair estilos para cores
        estilos = extrair_estilos_kml(root, ns)

        result = []

        for pm in placemarks:
            placemark_data = processar_placemark(pm, ns, estilos)
            if placemark_data:
                result.append(placemark_data)

        return result

    except Exception as e:
        print(f"Erro ao fazer parse do KML: {e}")
        return []


def extrair_estilos_kml(root, ns):
    """Extrai estilos definidos no KML para obter cores"""
    estilos = {}

    try:
        if ns:
            style_elements = root.findall('.//kml:Style', ns)
        else:
            style_elements = root.findall('.//*[local-name()="Style"]')

        for style in style_elements:
            style_id = style.get('id', '')
            if not style_id:
                continue

            # Buscar cor da linha ou polígono
            cor = None

            # PolyStyle
            if ns:
                poly_color = style.find('.//kml:PolyStyle/kml:color', ns)
            else:
                poly_color = style.find('.//*[local-name()="PolyStyle"]/*[local-name()="color"]')

            if poly_color is not None and poly_color.text:
                cor = converter_cor_kml_para_hex(poly_color.text)

            # LineStyle (fallback)
            if not cor:
                if ns:
                    line_color = style.find('.//kml:LineStyle/kml:color', ns)
                else:
                    line_color = style.find('.//*[local-name()="LineStyle"]/*[local-name()="color"]')

                if line_color is not None and line_color.text:
                    cor = converter_cor_kml_para_hex(line_color.text)

            if cor:
                estilos[style_id] = cor
                estilos[f"#{style_id}"] = cor

    except Exception:
        pass

    return estilos


def converter_cor_kml_para_hex(kml_color):
    """Converte cor KML (aabbggrr) para hex (#rrggbb)"""
    try:
        # KML usa formato aabbggrr (alpha, blue, green, red)
        if len(kml_color) == 8:
            aa = kml_color[0:2]
            bb = kml_color[2:4]
            gg = kml_color[4:6]
            rr = kml_color[6:8]
            return f"#{rr}{gg}{bb}"
        return None
    except Exception:
        return None


def processar_placemark(pm, ns, estilos):
    """Processa um Placemark e retorna dict com dados"""
    try:
        # Nome
        if ns:
            name_elem = pm.find('kml:name', ns)
        else:
            name_elem = pm.find('.//*[local-name()="name"]')

        name = name_elem.text if name_elem is not None and name_elem.text else 'Sem nome'

        # Descrição
        if ns:
            desc_elem = pm.find('kml:description', ns)
        else:
            desc_elem = pm.find('.//*[local-name()="description"]')

        description = ''
        if desc_elem is not None and desc_elem.text:
            # Limpar HTML se houver
            description = desc_elem.text.strip()
            if description.startswith('<'):
                from html import unescape
                import re
                description = re.sub('<[^<]+?>', '', unescape(description))

        # Estilo/Cor
        cor = '#00D4FF'  # Default
        if ns:
            style_url = pm.find('kml:styleUrl', ns)
        else:
            style_url = pm.find('.//*[local-name()="styleUrl"]')

        if style_url is not None and style_url.text:
            style_ref = style_url.text.strip()
            if style_ref in estilos:
                cor = estilos[style_ref]

        # Processar geometrias
        geometry = None
        tipo = None

        # Polygon
        if ns:
            polygon = pm.find('.//kml:Polygon', ns)
        else:
            polygon = pm.find('.//*[local-name()="Polygon"]')

        if polygon is not None:
            coords = extrair_coordenadas_polygon(polygon, ns)
            if coords:
                geometry = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [coords]
                    },
                    "properties": {"name": name}
                }
                tipo = "polygon"

        # LineString
        if geometry is None:
            if ns:
                linestring = pm.find('.//kml:LineString', ns)
            else:
                linestring = pm.find('.//*[local-name()="LineString"]')

            if linestring is not None:
                coords = extrair_coordenadas_simples(linestring, ns)
                if coords:
                    geometry = {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": coords
                        },
                        "properties": {"name": name}
                    }
                    tipo = "polyline"

        # Point
        if geometry is None:
            if ns:
                point = pm.find('.//kml:Point', ns)
            else:
                point = pm.find('.//*[local-name()="Point"]')

            if point is not None:
                coords = extrair_coordenadas_simples(point, ns)
                if coords and len(coords) > 0:
                    geometry = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": coords[0] if isinstance(coords[0], list) else coords
                        },
                        "properties": {"name": name}
                    }
                    tipo = "marker"

        # MultiGeometry (processar primeiro elemento)
        if geometry is None:
            if ns:
                multigeom = pm.find('.//kml:MultiGeometry', ns)
            else:
                multigeom = pm.find('.//*[local-name()="MultiGeometry"]')

            if multigeom is not None:
                # Processar como placemark recursivamente pegando primeiro elemento
                result = processar_multigeometry(multigeom, ns, name, description, cor, estilos)
                if result:
                    return result

        if geometry is None:
            return None

        return {
            'name': name,
            'description': description,
            'geometry': geometry,
            'type': tipo,
            'color': cor,
        }

    except Exception as e:
        print(f"Erro ao processar placemark: {e}")
        return None


def processar_multigeometry(multigeom, ns, name, description, cor, estilos):
    """Processa MultiGeometry extraindo todas as geometrias"""
    try:
        geometries = []

        # Polygons
        if ns:
            polygons = multigeom.findall('.//kml:Polygon', ns)
        else:
            polygons = multigeom.findall('.//*[local-name()="Polygon"]')

        for poly in polygons:
            coords = extrair_coordenadas_polygon(poly, ns)
            if coords:
                geometries.append({
                    "type": "Polygon",
                    "coordinates": [coords]
                })

        # LineStrings
        if ns:
            lines = multigeom.findall('.//kml:LineString', ns)
        else:
            lines = multigeom.findall('.//*[local-name()="LineString"]')

        for line in lines:
            coords = extrair_coordenadas_simples(line, ns)
            if coords:
                geometries.append({
                    "type": "LineString",
                    "coordinates": coords
                })

        # Points
        if ns:
            points = multigeom.findall('.//kml:Point', ns)
        else:
            points = multigeom.findall('.//*[local-name()="Point"]')

        for point in points:
            coords = extrair_coordenadas_simples(point, ns)
            if coords:
                coord = coords[0] if isinstance(coords[0], list) else coords
                geometries.append({
                    "type": "Point",
                    "coordinates": coord
                })

        if not geometries:
            return None

        # Se só tem uma geometria, usar diretamente
        if len(geometries) == 1:
            geom = geometries[0]
            tipo = "polygon" if geom["type"] == "Polygon" else ("polyline" if geom["type"] == "LineString" else "marker")
            return {
                'name': name,
                'description': description,
                'geometry': {
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {"name": name}
                },
                'type': tipo,
                'color': cor,
            }

        # Múltiplas geometrias - criar GeometryCollection
        return {
            'name': name,
            'description': description,
            'geometry': {
                "type": "Feature",
                "geometry": {
                    "type": "GeometryCollection",
                    "geometries": geometries
                },
                "properties": {"name": name}
            },
            'type': 'polygon',  # Default para multigeometry
            'color': cor,
        }

    except Exception:
        return None


def extrair_coordenadas_polygon(polygon, ns):
    """Extrai coordenadas de um Polygon KML"""
    try:
        if ns:
            coords_elem = polygon.find('.//kml:coordinates', ns)
        else:
            coords_elem = polygon.find('.//*[local-name()="coordinates"]')

        if coords_elem is None or not coords_elem.text:
            return None

        return parse_coordenadas_kml(coords_elem.text)

    except Exception:
        return None


def extrair_coordenadas_simples(element, ns):
    """Extrai coordenadas de elemento simples (Point, LineString)"""
    try:
        if ns:
            coords_elem = element.find('.//kml:coordinates', ns)
        else:
            coords_elem = element.find('.//*[local-name()="coordinates"]')

        if coords_elem is None or not coords_elem.text:
            return None

        return parse_coordenadas_kml(coords_elem.text)

    except Exception:
        return None


def parse_coordenadas_kml(coords_text):
    """Parse string de coordenadas KML para array GeoJSON.

    KML: "lng,lat,alt lng,lat,alt ..."
    GeoJSON: [[lng, lat], [lng, lat], ...]
    """
    try:
        coords_text = coords_text.strip()

        # Dividir por espaços ou quebras de linha
        parts = coords_text.replace('\n', ' ').replace('\t', ' ').split()

        coordinates = []
        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Cada coordenada é "lng,lat" ou "lng,lat,alt"
            values = part.split(',')
            if len(values) >= 2:
                lng = float(values[0])
                lat = float(values[1])
                coordinates.append([lng, lat])

        return coordinates if coordinates else None

    except Exception:
        return None


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
# APIs de Gerenciamento de Áreas Importadas
# ============================================

@csrf_exempt
@api_login_required
@require_http_methods(["DELETE", "POST"])
def api_excluir_area(request, area_id):
    """Excluir uma área de observação específica."""
    try:
        area = AreaObservacao.objects.get(id=area_id)
        nome = area.nome
        area.delete()

        return JsonResponse({
            'success': True,
            'mensagem': f'Área "{nome}" excluída com sucesso'
        })

    except AreaObservacao.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Área não encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@api_login_required
@require_http_methods(["DELETE", "POST"])
def api_excluir_grupo_importacao(request, grupo_id):
    """Excluir todas as áreas de um grupo de importação (arquivo KML/KMZ)."""
    try:
        areas = AreaObservacao.objects.filter(grupo_importacao=grupo_id)
        count = areas.count()

        if count == 0:
            return JsonResponse({
                'success': False,
                'error': 'Nenhuma área encontrada para este grupo de importação'
            }, status=404)

        # Obter nome do arquivo para mensagem
        primeira_area = areas.first()
        arquivo = primeira_area.arquivo_origem if primeira_area else 'desconhecido'

        areas.delete()

        return JsonResponse({
            'success': True,
            'mensagem': f'{count} áreas do arquivo "{arquivo}" excluídas com sucesso'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@api_login_required
@require_http_methods(["DELETE"])
def api_excluir_todas_areas(request):
    """Excluir TODAS as áreas de observação (limpeza geral)."""
    try:
        cliente = Cliente.objects.filter(ativo=True).first()
        if not cliente:
            return JsonResponse({'success': False, 'error': 'Cliente não configurado'}, status=400)

        areas = AreaObservacao.objects.filter(cliente=cliente)
        count = areas.count()

        if count == 0:
            return JsonResponse({
                'success': False,
                'error': 'Nenhuma área encontrada para excluir'
            }, status=404)

        areas.delete()

        return JsonResponse({
            'success': True,
            'mensagem': f'{count} áreas excluídas com sucesso'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@api_login_required
@require_http_methods(["POST", "PATCH"])
def api_toggle_area_ativa(request, area_id):
    """Ativar ou desativar uma área de observação."""
    try:
        area = AreaObservacao.objects.get(id=area_id)

        # Se enviou JSON, usar valor especificado
        if request.body:
            try:
                data = json.loads(request.body)
                area.ativa = data.get('ativa', not area.ativa)
            except json.JSONDecodeError:
                area.ativa = not area.ativa
        else:
            # Toggle simples
            area.ativa = not area.ativa

        area.save()

        return JsonResponse({
            'success': True,
            'area_id': str(area.id),
            'ativa': area.ativa,
            'mensagem': f'Área "{area.nome}" {"ativada" if area.ativa else "desativada"}'
        })

    except AreaObservacao.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Área não encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_login_required
@require_http_methods(["GET"])
def api_listar_importacoes(request):
    """Lista arquivos KML/KMZ importados agrupados.

    Retorna grupos de importação com suas áreas.
    """
    try:
        from django.db.models import Count, Min, Max

        # Agregar áreas por grupo de importação
        grupos = AreaObservacao.objects.filter(
            importada_de_kml=True,
            grupo_importacao__isnull=False
        ).values(
            'grupo_importacao',
            'arquivo_origem'
        ).annotate(
            total_areas=Count('id'),
            data_importacao=Min('criado_em'),
            evento_inicio=Min('evento_inicio'),
            evento_fim=Max('evento_fim'),
            temporaria=Max('temporaria')  # Se alguma é temporária, marca como temporária
        ).order_by('-data_importacao')

        importacoes = []
        for grupo in grupos:
            # Verificar se todas as áreas estão ativas
            areas_grupo = AreaObservacao.objects.filter(grupo_importacao=grupo['grupo_importacao'])
            todas_ativas = all(a.ativa for a in areas_grupo)

            importacoes.append({
                'grupo_id': grupo['grupo_importacao'],
                'arquivo': grupo['arquivo_origem'],
                'total_areas': grupo['total_areas'],
                'data_importacao': grupo['data_importacao'].isoformat() if grupo['data_importacao'] else None,
                'temporaria': bool(grupo['temporaria']),
                'evento_inicio': grupo['evento_inicio'].isoformat() if grupo['evento_inicio'] else None,
                'evento_fim': grupo['evento_fim'].isoformat() if grupo['evento_fim'] else None,
                'ativa': todas_ativas,
            })

        return JsonResponse({
            'success': True,
            'importacoes': importacoes,
            'total': len(importacoes)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@api_login_required
@require_http_methods(["POST", "PATCH"])
def api_atualizar_agendamento_grupo(request, grupo_id):
    """Atualizar datas de agendamento de um grupo de importação."""
    try:
        from django.utils import timezone
        from datetime import datetime

        data = json.loads(request.body)

        areas = AreaObservacao.objects.filter(grupo_importacao=grupo_id)
        if not areas.exists():
            return JsonResponse({
                'success': False,
                'error': 'Grupo não encontrado'
            }, status=404)

        # Processar datas
        evento_inicio = data.get('evento_inicio')
        evento_fim = data.get('evento_fim')
        temporaria = data.get('temporaria')

        if evento_inicio:
            try:
                evento_inicio = datetime.fromisoformat(evento_inicio.replace('Z', '+00:00'))
                if timezone.is_naive(evento_inicio):
                    evento_inicio = timezone.make_aware(evento_inicio)
            except (ValueError, TypeError):
                evento_inicio = None

        if evento_fim:
            try:
                evento_fim = datetime.fromisoformat(evento_fim.replace('Z', '+00:00'))
                if timezone.is_naive(evento_fim):
                    evento_fim = timezone.make_aware(evento_fim)
            except (ValueError, TypeError):
                evento_fim = None

        # Atualizar todas as áreas do grupo
        update_fields = {}
        if evento_inicio is not None:
            update_fields['evento_inicio'] = evento_inicio
        if evento_fim is not None:
            update_fields['evento_fim'] = evento_fim
        if temporaria is not None:
            update_fields['temporaria'] = temporaria

        if update_fields:
            areas.update(**update_fields)

        return JsonResponse({
            'success': True,
            'mensagem': f'Agendamento atualizado para {areas.count()} áreas',
            'areas_atualizadas': areas.count()
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
