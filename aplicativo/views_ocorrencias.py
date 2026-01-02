"""
Views para o Sistema de Gerenciamento de Ocorrências
IntegraCity - Command Center
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
import requests
import json

from .models import (
    OcorrenciaGerenciada,
    CategoriaOcorrencia,
    ProcedimentoOperacional,
    AgenciaResponsavel,
    HistoricoOcorrenciaGerenciada,
    AnexoOcorrenciaGerenciada,
    AgenciaOcorrencia,
    AuditLog
)

User = get_user_model()


@login_required
def ocorrencias_dashboard(request):
    """Dashboard principal de ocorrências"""

    # Estatísticas gerais
    stats = {
        'total': OcorrenciaGerenciada.objects.count(),
        'abertas': OcorrenciaGerenciada.objects.filter(status='aberta').count(),
        'em_andamento': OcorrenciaGerenciada.objects.filter(status='em_andamento').count(),
        'aguardando': OcorrenciaGerenciada.objects.filter(status='aguardando').count(),
        'fechadas': OcorrenciaGerenciada.objects.filter(status='fechada').count(),
        'criticas': OcorrenciaGerenciada.objects.filter(prioridade='critica').count(),
        'hoje': OcorrenciaGerenciada.objects.filter(
            data_abertura__date=timezone.now().date()
        ).count(),
    }

    # Ocorrências por categoria
    categorias_qs = CategoriaOcorrencia.objects.annotate(
        total=Count('ocorrencias_gerenciadas')
    ).filter(ativa=True).values('id', 'nome', 'total', 'cor', 'icone')

    # Converter UUID para string para serialização JSON
    por_categoria = []
    for cat in categorias_qs:
        cat['id'] = str(cat['id'])
        por_categoria.append(cat)

    # Ocorrências por status
    por_status = []
    for status_code, status_label in OcorrenciaGerenciada.STATUS_CHOICES:
        count = OcorrenciaGerenciada.objects.filter(status=status_code).count()
        por_status.append({
            'status': status_code,
            'label': status_label,
            'total': count
        })

    # Ocorrências por prioridade
    por_prioridade = []
    cores_prioridade = {
        'baixa': '#4CAF50',
        'media': '#00D4FF',
        'alta': '#FFB800',
        'critica': '#EF4444'
    }
    for prioridade_code, prioridade_label in OcorrenciaGerenciada.PRIORIDADE_CHOICES:
        count = OcorrenciaGerenciada.objects.filter(prioridade=prioridade_code).count()
        por_prioridade.append({
            'prioridade': prioridade_code,
            'label': prioridade_label,
            'total': count,
            'cor': cores_prioridade.get(prioridade_code, '#00D4FF')
        })

    # Ocorrências recentes (10 últimas)
    recentes = OcorrenciaGerenciada.objects.select_related(
        'categoria', 'procedimento', 'aberto_por', 'responsavel'
    ).order_by('-data_abertura')[:10]

    # Ocorrências críticas abertas
    criticas_abertas = OcorrenciaGerenciada.objects.filter(
        prioridade='critica',
        status__in=['aberta', 'em_andamento']
    ).select_related('categoria').order_by('-data_abertura')[:5]

    context = {
        'stats': stats,
        'por_categoria': por_categoria,
        'por_status': por_status,
        'por_prioridade': por_prioridade,
        'recentes': recentes,
        'criticas_abertas': criticas_abertas,
        'categorias_json': json.dumps(por_categoria),
    }

    return render(request, 'ocorrencias/dashboard.html', context)


@login_required
def ocorrencias_lista(request):
    """Lista de ocorrências com filtros e paginação"""

    ocorrencias = OcorrenciaGerenciada.objects.select_related(
        'categoria', 'procedimento', 'aberto_por', 'responsavel'
    ).prefetch_related('agencias')

    # Filtros
    status_filter = request.GET.get('status', '')
    prioridade_filter = request.GET.get('prioridade', '')
    categoria_filter = request.GET.get('categoria', '')
    origem_filter = request.GET.get('origem', '')
    search = request.GET.get('search', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')

    if status_filter:
        ocorrencias = ocorrencias.filter(status=status_filter)

    if prioridade_filter:
        ocorrencias = ocorrencias.filter(prioridade=prioridade_filter)

    if categoria_filter:
        ocorrencias = ocorrencias.filter(categoria_id=categoria_filter)

    if origem_filter:
        ocorrencias = ocorrencias.filter(origem=origem_filter)

    if search:
        ocorrencias = ocorrencias.filter(
            Q(numero_protocolo__icontains=search) |
            Q(titulo__icontains=search) |
            Q(descricao__icontains=search) |
            Q(endereco__icontains=search) |
            Q(bairro__icontains=search) |
            Q(solicitante_nome__icontains=search)
        )

    if data_inicio:
        ocorrencias = ocorrencias.filter(data_abertura__date__gte=data_inicio)

    if data_fim:
        ocorrencias = ocorrencias.filter(data_abertura__date__lte=data_fim)

    # Ordenação
    ordem = request.GET.get('ordem', '-data_abertura')
    ocorrencias = ocorrencias.order_by(ordem)

    # Paginação
    paginator = Paginator(ocorrencias, 20)
    page = request.GET.get('page', 1)
    ocorrencias_page = paginator.get_page(page)

    # Dados para filtros
    categorias = CategoriaOcorrencia.objects.filter(ativa=True)

    context = {
        'ocorrencias': ocorrencias_page,
        'categorias': categorias,
        'status_choices': OcorrenciaGerenciada.STATUS_CHOICES,
        'prioridade_choices': OcorrenciaGerenciada.PRIORIDADE_CHOICES,
        'origem_choices': OcorrenciaGerenciada.ORIGEM_CHOICES,
        'status_filter': status_filter,
        'prioridade_filter': prioridade_filter,
        'categoria_filter': categoria_filter,
        'origem_filter': origem_filter,
        'search': search,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'ordem': ordem,
        'total_resultados': paginator.count,
    }

    return render(request, 'ocorrencias/lista.html', context)


@login_required
def ocorrencia_criar(request):
    """Criar nova ocorrência"""

    if request.method == 'POST':
        try:
            # Processar dados do formulário
            categoria_id = request.POST.get('categoria')
            procedimento_id = request.POST.get('procedimento')

            ocorrencia = OcorrenciaGerenciada(
                categoria_id=categoria_id,
                procedimento_id=procedimento_id if procedimento_id else None,
                titulo=request.POST.get('titulo'),
                descricao=request.POST.get('descricao'),
                origem=request.POST.get('origem'),
                prioridade=request.POST.get('prioridade', 'media'),
                endereco=request.POST.get('endereco', ''),
                bairro=request.POST.get('bairro', ''),
                cep=request.POST.get('cep', ''),
                referencia=request.POST.get('referencia', ''),
                solicitante_nome=request.POST.get('solicitante_nome', ''),
                solicitante_telefone=request.POST.get('solicitante_telefone', ''),
                solicitante_email=request.POST.get('solicitante_email', ''),
                observacoes=request.POST.get('observacoes', ''),
                aberto_por=request.user,
            )

            # Coordenadas
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            if latitude and longitude:
                try:
                    ocorrencia.latitude = float(latitude)
                    ocorrencia.longitude = float(longitude)
                except (ValueError, TypeError):
                    pass

            # Responsável - sempre é o usuário logado ao criar
            ocorrencia.responsavel = request.user

            ocorrencia.save()

            # Adicionar agências
            agencias_ids = request.POST.getlist('agencias')
            if agencias_ids:
                ocorrencia.agencias.set(agencias_ids)

            # Criar registro no histórico
            HistoricoOcorrenciaGerenciada.objects.create(
                ocorrencia=ocorrencia,
                tipo='criacao',
                descricao=f'Ocorrência criada por {request.user.get_full_name() or request.user.username}',
                usuario=request.user
            )

            # Processar anexos
            for arquivo in request.FILES.getlist('anexos'):
                tipo = 'foto' if arquivo.content_type.startswith('image/') else 'documento'
                if arquivo.content_type.startswith('video/'):
                    tipo = 'video'
                elif arquivo.content_type.startswith('audio/'):
                    tipo = 'audio'

                anexo = AnexoOcorrenciaGerenciada.objects.create(
                    ocorrencia=ocorrencia,
                    tipo=tipo,
                    arquivo=arquivo,
                    nome_original=arquivo.name,
                    tamanho=arquivo.size,
                    uploaded_por=request.user
                )

                # Histórico do anexo
                HistoricoOcorrenciaGerenciada.objects.create(
                    ocorrencia=ocorrencia,
                    tipo='anexo',
                    descricao=f'Anexo "{arquivo.name}" adicionado',
                    usuario=request.user
                )

            # Log de auditoria
            AuditLog.log(
                request,
                'create',
                'ocorrencia',
                str(ocorrencia.id),
                {'protocolo': ocorrencia.numero_protocolo}
            )

            # Recalcular estágio operacional da cidade
            try:
                from .services.motor_decisao import MotorDecisao
                motor = MotorDecisao()
                motor.calcular_nivel_cidade(usuario=request.user)
            except Exception as e:
                # Log do erro mas não impede a criação da ocorrência
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Erro ao recalcular estágio após criar ocorrência: {e}")

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Ocorrência {ocorrencia.numero_protocolo} criada com sucesso!',
                    'protocolo': ocorrencia.numero_protocolo,
                    'id': str(ocorrencia.id)
                })

            return redirect('ocorrencia_detalhe', ocorrencia_id=ocorrencia.id)

        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            raise

    # GET - Exibir formulário
    categorias = CategoriaOcorrencia.objects.filter(ativa=True).order_by('ordem', 'nome')
    procedimentos = ProcedimentoOperacional.objects.filter(ativo=True).select_related('categoria')
    agencias = AgenciaResponsavel.objects.filter(ativa=True).order_by('nome')
    usuarios = User.objects.filter(is_active=True).order_by('first_name', 'username')

    # Organizar POPs por categoria
    pops_por_categoria = {}
    for pop in procedimentos:
        cat_id = str(pop.categoria_id)
        if cat_id not in pops_por_categoria:
            pops_por_categoria[cat_id] = []
        pops_por_categoria[cat_id].append({
            'id': str(pop.id),
            'codigo': pop.codigo,
            'titulo': pop.titulo
        })

    context = {
        'categorias': categorias,
        'procedimentos': procedimentos,
        'agencias': agencias,
        'usuarios': usuarios,
        'origem_choices': OcorrenciaGerenciada.ORIGEM_CHOICES,
        'prioridade_choices': OcorrenciaGerenciada.PRIORIDADE_CHOICES,
        'pops_por_categoria': json.dumps(pops_por_categoria),
    }

    return render(request, 'ocorrencias/criar.html', context)


@login_required
def ocorrencia_detalhe(request, ocorrencia_id):
    """Visualizar detalhes da ocorrência"""

    ocorrencia = get_object_or_404(
        OcorrenciaGerenciada.objects.select_related(
            'categoria', 'procedimento', 'aberto_por', 'responsavel'
        ).prefetch_related('agencias', 'historico', 'anexos', 'agencias_acionadas__agencia'),
        id=ocorrencia_id
    )

    # Histórico ordenado
    historico = ocorrencia.historico.select_related('usuario').order_by('-timestamp')

    # Anexos
    anexos = ocorrencia.anexos.select_related('uploaded_por').order_by('-uploaded_at')

    # Agências acionadas (com o novo modelo)
    agencias_acionadas = ocorrencia.agencias_acionadas.select_related(
        'agencia', 'acionado_por'
    ).order_by('-data_acionamento')

    # Estatísticas da ocorrência
    tempo_aberto = None
    if ocorrencia.status not in ['fechada', 'cancelada']:
        tempo_aberto = timezone.now() - ocorrencia.data_abertura

    context = {
        'ocorrencia': ocorrencia,
        'historico': historico,
        'anexos': anexos,
        'agencias_acionadas': agencias_acionadas,
        'tempo_aberto': tempo_aberto,
        'status_choices': OcorrenciaGerenciada.STATUS_CHOICES,
        'agencia_status_choices': AgenciaOcorrencia.STATUS_CHOICES,
    }

    return render(request, 'ocorrencias/detalhe.html', context)


@login_required
def ocorrencia_editar(request, ocorrencia_id):
    """Editar ocorrência existente"""

    ocorrencia = get_object_or_404(
        OcorrenciaGerenciada.objects.select_related('categoria', 'procedimento'),
        id=ocorrencia_id
    )

    if request.method == 'POST':
        try:
            # Registrar alterações
            alteracoes = {}

            # Campos que podem ser alterados
            campos_editaveis = [
                'titulo', 'descricao', 'prioridade', 'status', 'endereco',
                'bairro', 'cep', 'referencia', 'observacoes',
                'solicitante_nome', 'solicitante_telefone', 'solicitante_email'
            ]

            for campo in campos_editaveis:
                valor_antigo = getattr(ocorrencia, campo)
                valor_novo = request.POST.get(campo, valor_antigo)
                if str(valor_antigo) != str(valor_novo):
                    alteracoes[campo] = {
                        'antes': valor_antigo,
                        'depois': valor_novo
                    }
                    setattr(ocorrencia, campo, valor_novo)

            # Categoria
            categoria_id = request.POST.get('categoria')
            if categoria_id and str(ocorrencia.categoria_id) != categoria_id:
                alteracoes['categoria'] = {
                    'antes': str(ocorrencia.categoria),
                    'depois': categoria_id
                }
                ocorrencia.categoria_id = categoria_id

            # Procedimento
            procedimento_id = request.POST.get('procedimento')
            if procedimento_id:
                if str(ocorrencia.procedimento_id) != procedimento_id:
                    alteracoes['procedimento'] = {
                        'antes': str(ocorrencia.procedimento) if ocorrencia.procedimento else None,
                        'depois': procedimento_id
                    }
                    ocorrencia.procedimento_id = procedimento_id
            else:
                if ocorrencia.procedimento:
                    alteracoes['procedimento'] = {
                        'antes': str(ocorrencia.procedimento),
                        'depois': None
                    }
                ocorrencia.procedimento = None

            # Responsável
            responsavel_id = request.POST.get('responsavel')
            if responsavel_id:
                if str(ocorrencia.responsavel_id) != responsavel_id:
                    alteracoes['responsavel'] = {
                        'antes': str(ocorrencia.responsavel) if ocorrencia.responsavel else None,
                        'depois': responsavel_id
                    }
                    ocorrencia.responsavel_id = responsavel_id
            else:
                if ocorrencia.responsavel:
                    alteracoes['responsavel'] = {
                        'antes': str(ocorrencia.responsavel),
                        'depois': None
                    }
                ocorrencia.responsavel = None

            # Coordenadas
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            if latitude and longitude:
                try:
                    ocorrencia.latitude = float(latitude)
                    ocorrencia.longitude = float(longitude)
                except (ValueError, TypeError):
                    pass

            # Verificar mudança de status
            status_anterior = OcorrenciaGerenciada.objects.get(id=ocorrencia_id).status
            if ocorrencia.status != status_anterior:
                # Se foi fechada, registrar data de conclusão
                if ocorrencia.status == 'fechada':
                    ocorrencia.data_conclusao = timezone.now()

            ocorrencia.save()

            # Atualizar agências
            agencias_ids = request.POST.getlist('agencias')
            ocorrencia.agencias.set(agencias_ids)

            # Determinar tipo de histórico
            if 'status' in alteracoes:
                tipo_historico = 'mudanca_status'
                descricao = f'Status alterado de "{alteracoes["status"]["antes"]}" para "{alteracoes["status"]["depois"]}"'
            elif 'responsavel' in alteracoes:
                tipo_historico = 'atribuicao'
                descricao = f'Ocorrência atribuída/reatribuída'
            else:
                tipo_historico = 'atualizacao'
                descricao = f'Ocorrência atualizada por {request.user.get_full_name() or request.user.username}'

            # Criar histórico
            if alteracoes:
                HistoricoOcorrenciaGerenciada.objects.create(
                    ocorrencia=ocorrencia,
                    tipo=tipo_historico,
                    descricao=descricao,
                    dados_alterados=alteracoes,
                    usuario=request.user
                )

            # Processar novos anexos
            for arquivo in request.FILES.getlist('anexos'):
                tipo = 'foto' if arquivo.content_type.startswith('image/') else 'documento'
                if arquivo.content_type.startswith('video/'):
                    tipo = 'video'
                elif arquivo.content_type.startswith('audio/'):
                    tipo = 'audio'

                AnexoOcorrenciaGerenciada.objects.create(
                    ocorrencia=ocorrencia,
                    tipo=tipo,
                    arquivo=arquivo,
                    nome_original=arquivo.name,
                    tamanho=arquivo.size,
                    uploaded_por=request.user
                )

                HistoricoOcorrenciaGerenciada.objects.create(
                    ocorrencia=ocorrencia,
                    tipo='anexo',
                    descricao=f'Anexo "{arquivo.name}" adicionado',
                    usuario=request.user
                )

            # Log de auditoria
            AuditLog.log(
                request,
                'update',
                'ocorrencia',
                str(ocorrencia.id),
                {'alteracoes': alteracoes}
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Ocorrência atualizada com sucesso!'
                })

            return redirect('ocorrencia_detalhe', ocorrencia_id=ocorrencia.id)

        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            raise

    # GET - Formulário de edição
    categorias = CategoriaOcorrencia.objects.filter(ativa=True).order_by('ordem', 'nome')
    procedimentos = ProcedimentoOperacional.objects.filter(ativo=True).select_related('categoria')
    agencias = AgenciaResponsavel.objects.filter(ativa=True).order_by('nome')
    usuarios = User.objects.filter(is_active=True).order_by('first_name', 'username')

    # POPs por categoria
    pops_por_categoria = {}
    for pop in procedimentos:
        cat_id = str(pop.categoria_id)
        if cat_id not in pops_por_categoria:
            pops_por_categoria[cat_id] = []
        pops_por_categoria[cat_id].append({
            'id': str(pop.id),
            'codigo': pop.codigo,
            'titulo': pop.titulo
        })

    context = {
        'ocorrencia': ocorrencia,
        'categorias': categorias,
        'procedimentos': procedimentos,
        'agencias': agencias,
        'usuarios': usuarios,
        'origem_choices': OcorrenciaGerenciada.ORIGEM_CHOICES,
        'prioridade_choices': OcorrenciaGerenciada.PRIORIDADE_CHOICES,
        'status_choices': OcorrenciaGerenciada.STATUS_CHOICES,
        'pops_por_categoria': json.dumps(pops_por_categoria),
        'agencias_selecionadas': [str(ag_id) for ag_id in ocorrencia.agencias.values_list('id', flat=True)],
    }

    return render(request, 'ocorrencias/editar.html', context)


@login_required
@require_http_methods(["POST"])
def ocorrencia_atualizar_status(request, ocorrencia_id):
    """API para atualizar status da ocorrência rapidamente"""

    ocorrencia = get_object_or_404(OcorrenciaGerenciada, id=ocorrencia_id)

    try:
        data = json.loads(request.body)
        novo_status = data.get('status')

        if novo_status not in dict(OcorrenciaGerenciada.STATUS_CHOICES):
            return JsonResponse({
                'success': False,
                'error': 'Status inválido'
            }, status=400)

        status_anterior = ocorrencia.status
        ocorrencia.status = novo_status

        if novo_status == 'fechada':
            ocorrencia.data_conclusao = timezone.now()

        ocorrencia.save()

        # Histórico
        HistoricoOcorrenciaGerenciada.objects.create(
            ocorrencia=ocorrencia,
            tipo='mudanca_status',
            descricao=f'Status alterado de "{status_anterior}" para "{novo_status}"',
            dados_alterados={
                'status': {'antes': status_anterior, 'depois': novo_status}
            },
            usuario=request.user
        )

        return JsonResponse({
            'success': True,
            'message': f'Status atualizado para {novo_status}',
            'novo_status': novo_status,
            'status_display': dict(OcorrenciaGerenciada.STATUS_CHOICES)[novo_status]
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def ocorrencia_adicionar_comentario(request, ocorrencia_id):
    """API para adicionar comentário à ocorrência"""

    ocorrencia = get_object_or_404(OcorrenciaGerenciada, id=ocorrencia_id)

    try:
        data = json.loads(request.body)
        comentario = data.get('comentario', '').strip()

        if not comentario:
            return JsonResponse({
                'success': False,
                'error': 'Comentário não pode estar vazio'
            }, status=400)

        historico = HistoricoOcorrenciaGerenciada.objects.create(
            ocorrencia=ocorrencia,
            tipo='comentario',
            descricao=comentario,
            usuario=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Comentário adicionado com sucesso',
            'historico': {
                'id': str(historico.id),
                'tipo': historico.tipo,
                'descricao': historico.descricao,
                'usuario': request.user.get_full_name() or request.user.username,
                'timestamp': historico.timestamp.strftime('%d/%m/%Y %H:%M')
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def buscar_cep(request):
    """API para buscar endereço por CEP usando ViaCEP"""

    cep = request.GET.get('cep', '').replace('-', '').replace('.', '').strip()

    if len(cep) != 8 or not cep.isdigit():
        return JsonResponse({
            'success': False,
            'error': 'CEP inválido. Deve conter 8 dígitos.'
        }, status=400)

    try:
        response = requests.get(
            f'https://viacep.com.br/ws/{cep}/json/',
            timeout=5
        )
        data = response.json()

        if 'erro' in data:
            return JsonResponse({
                'success': False,
                'error': 'CEP não encontrado'
            }, status=404)

        return JsonResponse({
            'success': True,
            'cep': data.get('cep', ''),
            'endereco': data.get('logradouro', ''),
            'complemento': data.get('complemento', ''),
            'bairro': data.get('bairro', ''),
            'cidade': data.get('localidade', ''),
            'uf': data.get('uf', ''),
        })

    except requests.Timeout:
        return JsonResponse({
            'success': False,
            'error': 'Tempo de resposta excedido'
        }, status=504)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao buscar CEP: {str(e)}'
        }, status=500)


@login_required
def api_ocorrencias_mapa(request):
    """API para retornar ocorrências para exibição no mapa"""

    # Filtrar ocorrências com coordenadas
    ocorrencias = OcorrenciaGerenciada.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('categoria').exclude(
        status__in=['fechada', 'cancelada']
    )

    # Filtros opcionais
    status_filter = request.GET.get('status')
    prioridade_filter = request.GET.get('prioridade')
    categoria_filter = request.GET.get('categoria')

    if status_filter:
        ocorrencias = ocorrencias.filter(status=status_filter)
    if prioridade_filter:
        ocorrencias = ocorrencias.filter(prioridade=prioridade_filter)
    if categoria_filter:
        ocorrencias = ocorrencias.filter(categoria_id=categoria_filter)

    data = []
    for oc in ocorrencias:
        data.append({
            'id': str(oc.id),
            'protocolo': oc.numero_protocolo,
            'titulo': oc.titulo,
            'latitude': float(oc.latitude),
            'longitude': float(oc.longitude),
            'status': oc.status,
            'status_display': oc.get_status_display(),
            'prioridade': oc.prioridade,
            'prioridade_display': oc.get_prioridade_display(),
            'categoria': oc.categoria.nome,
            'categoria_cor': oc.categoria.cor,
            'categoria_icone': oc.categoria.icone,
            'endereco': oc.endereco,
            'bairro': oc.bairro,
            'data_abertura': oc.data_abertura.strftime('%d/%m/%Y %H:%M'),
        })

    return JsonResponse({'success': True, 'data': data, 'total': len(data)})


@login_required
def api_pops_por_categoria(request, categoria_id):
    """API para retornar POPs de uma categoria específica"""

    pops = ProcedimentoOperacional.objects.filter(
        categoria_id=categoria_id,
        ativo=True
    ).order_by('codigo')

    data = []
    for pop in pops:
        data.append({
            'id': str(pop.id),
            'codigo': pop.codigo,
            'titulo': pop.titulo,
            'descricao': pop.descricao,
            'arquivo_path': pop.arquivo_path,
            'tempo_resposta_esperado': pop.tempo_resposta_esperado,
        })

    return JsonResponse({'success': True, 'data': data})


@login_required
def api_estatisticas_ocorrencias(request):
    """API para retornar estatísticas de ocorrências"""

    # Período (padrão: últimos 30 dias)
    dias = int(request.GET.get('dias', 30))
    data_inicio = timezone.now() - timezone.timedelta(days=dias)

    ocorrencias = OcorrenciaGerenciada.objects.filter(
        data_abertura__gte=data_inicio
    )

    # Estatísticas gerais
    stats = {
        'total': ocorrencias.count(),
        'abertas': ocorrencias.filter(status='aberta').count(),
        'em_andamento': ocorrencias.filter(status='em_andamento').count(),
        'fechadas': ocorrencias.filter(status='fechada').count(),
        'criticas': ocorrencias.filter(prioridade='critica').count(),
    }

    # Por categoria
    por_categoria = list(
        ocorrencias.values('categoria__nome', 'categoria__cor')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    # Por status
    por_status = list(
        ocorrencias.values('status')
        .annotate(total=Count('id'))
    )

    # Por prioridade
    por_prioridade = list(
        ocorrencias.values('prioridade')
        .annotate(total=Count('id'))
    )

    return JsonResponse({
        'success': True,
        'periodo_dias': dias,
        'stats': stats,
        'por_categoria': por_categoria,
        'por_status': por_status,
        'por_prioridade': por_prioridade,
    })


# ============================================
# GERENCIAMENTO DE AGÊNCIAS NA OCORRÊNCIA
# ============================================

@login_required
@require_http_methods(["POST"])
def ocorrencia_adicionar_agencia(request, ocorrencia_id):
    """Adicionar/Acionar uma agência na ocorrência"""

    ocorrencia = get_object_or_404(OcorrenciaGerenciada, id=ocorrencia_id)

    try:
        data = json.loads(request.body)
        agencia_id = data.get('agencia_id')
        observacoes = data.get('observacoes', '')

        if not agencia_id:
            return JsonResponse({
                'success': False,
                'error': 'ID da agência é obrigatório'
            }, status=400)

        agencia = get_object_or_404(AgenciaResponsavel, id=agencia_id)

        # Verificar se já existe
        if AgenciaOcorrencia.objects.filter(ocorrencia=ocorrencia, agencia=agencia).exists():
            return JsonResponse({
                'success': False,
                'error': f'A agência {agencia.sigla} já foi acionada nesta ocorrência'
            }, status=400)

        # Criar acionamento
        acionamento = AgenciaOcorrencia.objects.create(
            ocorrencia=ocorrencia,
            agencia=agencia,
            status='informada',
            acionado_por=request.user,
            observacoes=observacoes
        )

        # Histórico
        HistoricoOcorrenciaGerenciada.objects.create(
            ocorrencia=ocorrencia,
            tipo='atualizacao',
            descricao=f'Agência {agencia.sigla} ({agencia.nome}) acionada',
            usuario=request.user
        )

        return JsonResponse({
            'success': True,
            'message': f'Agência {agencia.sigla} acionada com sucesso!',
            'acionamento': {
                'id': str(acionamento.id),
                'agencia': {
                    'id': str(agencia.id),
                    'nome': agencia.nome,
                    'sigla': agencia.sigla,
                    'icone': agencia.icone,
                    'cor': agencia.cor
                },
                'status': acionamento.status,
                'status_display': acionamento.get_status_display(),
                'status_cor': acionamento.status_cor,
                'status_icone': acionamento.status_icone,
                'data_acionamento': acionamento.data_acionamento.strftime('%d/%m/%Y %H:%M'),
                'acionado_por': request.user.get_full_name() or request.user.username
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def ocorrencia_atualizar_agencia(request, ocorrencia_id, acionamento_id):
    """Atualizar status de uma agência na ocorrência"""

    ocorrencia = get_object_or_404(OcorrenciaGerenciada, id=ocorrencia_id)
    acionamento = get_object_or_404(AgenciaOcorrencia, id=acionamento_id, ocorrencia=ocorrencia)

    try:
        data = json.loads(request.body)
        novo_status = data.get('status')
        observacoes = data.get('observacoes')

        if novo_status and novo_status not in dict(AgenciaOcorrencia.STATUS_CHOICES):
            return JsonResponse({
                'success': False,
                'error': 'Status inválido'
            }, status=400)

        status_anterior = acionamento.status

        if novo_status:
            acionamento.status = novo_status

            # Atualizar datas conforme o status
            if novo_status == 'presente' and not acionamento.data_chegada:
                acionamento.data_chegada = timezone.now()
            elif novo_status in ['concluida', 'dispensada'] and not acionamento.data_conclusao:
                acionamento.data_conclusao = timezone.now()

        if observacoes is not None:
            acionamento.observacoes = observacoes

        acionamento.save()

        # Histórico
        if novo_status and status_anterior != novo_status:
            HistoricoOcorrenciaGerenciada.objects.create(
                ocorrencia=ocorrencia,
                tipo='atualizacao',
                descricao=f'Status da agência {acionamento.agencia.sigla} alterado de "{dict(AgenciaOcorrencia.STATUS_CHOICES)[status_anterior]}" para "{dict(AgenciaOcorrencia.STATUS_CHOICES)[novo_status]}"',
                usuario=request.user
            )

        return JsonResponse({
            'success': True,
            'message': f'Agência {acionamento.agencia.sigla} atualizada!',
            'status': acionamento.status,
            'status_display': acionamento.get_status_display(),
            'status_cor': acionamento.status_cor,
            'status_icone': acionamento.status_icone,
            'acionamento': {
                'id': str(acionamento.id),
                'status': acionamento.status,
                'status_display': acionamento.get_status_display(),
                'status_cor': acionamento.status_cor,
                'status_icone': acionamento.status_icone,
                'data_chegada': acionamento.data_chegada.strftime('%d/%m/%Y %H:%M') if acionamento.data_chegada else None,
                'data_conclusao': acionamento.data_conclusao.strftime('%d/%m/%Y %H:%M') if acionamento.data_conclusao else None,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
def ocorrencia_remover_agencia(request, ocorrencia_id, acionamento_id):
    """Remover uma agência da ocorrência"""

    ocorrencia = get_object_or_404(OcorrenciaGerenciada, id=ocorrencia_id)
    acionamento = get_object_or_404(AgenciaOcorrencia, id=acionamento_id, ocorrencia=ocorrencia)

    try:
        agencia_sigla = acionamento.agencia.sigla
        agencia_nome = acionamento.agencia.nome

        acionamento.delete()

        # Histórico
        HistoricoOcorrenciaGerenciada.objects.create(
            ocorrencia=ocorrencia,
            tipo='atualizacao',
            descricao=f'Agência {agencia_sigla} ({agencia_nome}) removida da ocorrência',
            usuario=request.user
        )

        return JsonResponse({
            'success': True,
            'message': f'Agência {agencia_sigla} removida da ocorrência'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def api_agencias_disponiveis(request, ocorrencia_id):
    """API para listar agências disponíveis para acionar (que ainda não foram acionadas)"""

    ocorrencia = get_object_or_404(OcorrenciaGerenciada, id=ocorrencia_id)

    # IDs das agências já acionadas
    agencias_acionadas_ids = AgenciaOcorrencia.objects.filter(
        ocorrencia=ocorrencia
    ).values_list('agencia_id', flat=True)

    # Agências disponíveis (ativas e não acionadas)
    agencias = AgenciaResponsavel.objects.filter(
        ativa=True
    ).exclude(
        id__in=agencias_acionadas_ids
    ).order_by('nome')

    data = []
    for ag in agencias:
        data.append({
            'id': str(ag.id),
            'nome': ag.nome,
            'sigla': ag.sigla,
            'icone': ag.icone,
            'cor': ag.cor,
            'telefone': ag.telefone,
        })

    return JsonResponse({'success': True, 'data': data})
