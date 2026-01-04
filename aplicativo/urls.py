from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from aplicativo import views
from aplicativo import views_users
from aplicativo import views_ocorrencias
from aplicativo import views_matriz
from aplicativo import views_meteorologia
from aplicativo import views_mobilidade
from aplicativo import views_areas
from aplicativo import views_eventos

urlpatterns = [
    # LOGIN - PÁGINA PRINCIPAL
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # ============================================
    # GERENCIAMENTO DE USUÁRIOS
    # ============================================
    path('usuarios/', views_users.user_management, name='usuarios_dashboard'),
    path('users/', views_users.user_management, name='user_management'),
    path('users/create/', views_users.user_create, name='user_create'),
    path('users/<int:user_id>/', views_users.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views_users.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views_users.user_delete, name='user_delete'),
    path('users/<int:user_id>/toggle/', views_users.user_toggle_status, name='user_toggle_status'),
    path('users/<int:user_id>/unlock/', views_users.user_unlock, name='user_unlock'),
    path('users/<int:user_id>/reset-password/', views_users.user_reset_password, name='user_reset_password'),
    path('users/<int:user_id>/permissions/', views_users.user_permissions, name='user_permissions'),
    path('users/<int:user_id>/modules/', views_users.user_module_permissions, name='user_module_permissions'),

    # APIs de Usuários
    path('api/users/<int:user_id>/modules/', views_users.api_user_module_permissions, name='api_user_module_permissions'),
    path('api/users/', views_users.api_users_list, name='api_users_list'),
    path('api/users/stats/', views_users.api_users_stats, name='api_users_stats'),

    # Logs de Auditoria
    path('audit/', views_users.audit_logs, name='audit_logs'),
    path('audit/<uuid:log_id>/detail/', views_users.audit_log_detail, name='audit_log_detail'),

    # Páginas
    path('home/', views.waze_dashboard_view, name='home'),
    path('waze-dashboard/', views.waze_dashboard_view, name='waze_dashboard'),
    path('cor/', views.cor_dashboard_view, name='cor_dashboard'),
    path('cor-hightech/', views.cor_dashboard_hightech_view, name='cor_dashboard_hightech'),
    path('api/estagio-externo/', views.estagio_proxy, name='estagio_proxy'),

    # ============================================
    # MOBILIDADE - INTEGRAÇÃO WAZE
    # ============================================
    path('mob/', views_mobilidade.mobilidade_dashboard, name='mobilidade_waze'),
    path('api/mob/coletar/', views_mobilidade.api_coletar_mobilidade_agora, name='api_coletar_mobilidade'),
    path('api/mob/nivel/', views_mobilidade.api_nivel_mobilidade, name='api_nivel_mobilidade'),
    path('api/mob/dados/', views_mobilidade.api_dados_mobilidade, name='api_dados_mobilidade'),
    path('api/mob/jams/', views_mobilidade.api_jams_mapa, name='api_jams_mapa'),
    path('api/mob/alerts/', views_mobilidade.api_alerts_mapa, name='api_alerts_mapa'),
    path('api/mob/resumo/', views_mobilidade.api_resumo_mobilidade, name='api_resumo_mobilidade'),
    path('api/mob/waze-completo/', views_mobilidade.api_waze_completo, name='api_waze_completo'),
    # APIs de mobilidade - vias e alertas
    path('api/mob/vias-engarrafadas/', views_mobilidade.api_vias_engarrafadas, name='api_vias_engarrafadas'),
    path('api/mob/alertas-categorizados/', views_mobilidade.api_alertas_categorizados, name='api_alertas_categorizados'),
    path('mob/vias/', views_mobilidade.vias_engarrafadas_view, name='vias_engarrafadas'),
    path('mob/alertas/', views_mobilidade.alertas_categorizados_view, name='alertas_categorizados'),
    # Manter URL antiga para compatibilidade
    path('mobilidade/', views.mobilidade_dashboard_view, name='mobilidade_dashboard'),

    # ============================================
    # METEOROLOGIA - INTEGRAÇÃO INMET
    # ============================================
    path('meteo/', views_meteorologia.meteorologia_dashboard, name='meteorologia_inmet'),
    path('api/meteo/coletar/', views_meteorologia.api_coletar_agora, name='api_coletar_meteorologia'),
    path('api/meteo/estacao/<str:codigo_inmet>/', views_meteorologia.api_dados_estacao, name='api_dados_estacao'),
    path('api/meteo/nivel/', views_meteorologia.api_nivel_meteorologia, name='api_nivel_meteorologia'),
    path('api/meteo/calor/', views_meteorologia.api_nivel_calor, name='api_nivel_calor'),

    # Manter URL antiga para compatibilidade
    path('meteorologia/', views.meteorologia_dashboard_view, name='meteorologia_dashboard'),

    # APIs - Sirenes
    path('api/sirenes/', views.sirene_api, name='sirene_api'),

    # APIs - Sirenes e Chuvas (Defesa Civil RJ - APIs externas)
    path('api/chuvas-defesa-civil/', views.api_chuvas_defesa_civil, name='api_chuvas_defesa_civil'),
    path('api/sirenes-defesa-civil/', views.api_sirenes_defesa_civil, name='api_sirenes_defesa_civil'),
    path('api/sirenes-chuvas/', views.api_sirenes_chuvas_combinado, name='api_sirenes_chuvas'),
    path('api/pluviometros-defesa-civil/', views.api_pluviometros_defesa_civil, name='api_pluviometros_defesa_civil'),
    # REMOVIDO: path('api/test/', ...) - API de teste removida por seguranca
    path('api/mobilidade/', views.mobilidade_api, name='api_mobilidade'),

    # APIs - Estágios
    path('api/estagio/', views.estagio_api, name='estagio_api'),
    path('api/estagio/app/', views.estagio_api_app, name='estagio_api_app'),
    path('api/estagio-atual/', views.api_estagio_atual, name='api_estagio_atual'),
    path('alertas_api/', views.alertas_api, name='alertas_api_compat'),
    path('estagio_api/', views.estagio_api, name='estagio_api_compat'),

    # APIs - Meteorologia
    path('api/chuva/', views.chuva_api, name='chuva_api'),
    path('api/alertas/', views.alertas_api, name='api_alertas'),
    path('api/calor/', views.calor_api, name='calor_api'),

    # APIs - Eventos
    path('api/eventos/', views.api_eventos, name='api_eventos'),

    # ============================================
    # GESTAO DE EVENTOS
    # ============================================
    path('eventos/', views_eventos.eventos_lista_view, name='eventos_lista'),
    path('eventos/cadastro/', views_eventos.eventos_cadastro_view, name='eventos_cadastro'),
    path('eventos/<int:evento_id>/', views_eventos.eventos_detalhe_view, name='eventos_detalhe'),
    path('eventos/<int:evento_id>/editar/', views_eventos.eventos_editar_view, name='eventos_editar'),

    # APIs de Eventos (novas)
    path('api/eventos/geojson/', views_eventos.api_eventos_geojson, name='api_eventos_geojson'),
    path('api/eventos/lista/', views_eventos.api_eventos_lista, name='api_eventos_lista'),
    path('api/eventos/timeline/', views_eventos.api_eventos_timeline, name='api_eventos_timeline'),
    path('api/eventos/estatisticas/', views_eventos.api_eventos_estatisticas, name='api_eventos_estatisticas'),
    path('api/eventos/<int:evento_id>/', views_eventos.api_evento_detalhe, name='api_evento_detalhe'),
    path('api/eventos/criar/', views_eventos.api_evento_criar, name='api_evento_criar'),
    path('api/eventos/<int:evento_id>/atualizar/', views_eventos.api_evento_atualizar, name='api_evento_atualizar'),
    path('api/eventos/<int:evento_id>/excluir/', views_eventos.api_evento_excluir, name='api_evento_excluir'),

    # APIs - Locais
    path('api/escolas/', views.escolas_view, name='escolas'),
    path('api/hospitais/', views.api_hospitais, name='api_hospitais'),
    path('api/pluviometros/', views.api_pluviometros, name='pluviometros'),

    # APIs - Edificações e Dispositivos IoT
    path('api/edificacoes/', views.api_edificacoes, name='api_edificacoes'),
    path('api/edificacoes/<int:edificacao_id>/', views.api_edificacao_detalhe, name='api_edificacao_detalhe'),
    path('api/escolas/<int:escola_id>/dispositivos/', views.api_escola_dispositivos, name='api_escola_dispositivos'),
    path('api/dispositivo/<int:dispositivo_id>/snapshot/', views.api_dispositivo_snapshot, name='api_dispositivo_snapshot'),
    path('api/ventos/', views.estacoes_vento_view, name='ventos'),
    path('api/bens-tombados/', views.bens_tombados_view, name='bens_tombados'),

    # APIs - Cameras
    path('videomonitoramento/', views.videomonitoramento, name='videomonitoramento'),
    path('api/cameras/', views.cameras_api_local, name='cameras_api'),

    # Manter compatibilidade com URLs antigas
    path('hls/<str:camera_id>/playlist.m3u8', views.camera_hls_placeholder, name='hls_placeholder'),

    # Novas rotas de verificação de câmeras
    path('api/cameras/status/', views.cameras_status, name='cameras_status'),
    path('api/cameras/ping/', views.ping_camera, name='ping_camera'),

    # APIs de Câmeras
    path('api/camera/<str:camera_id>/snapshot/', views.camera_snapshot, name='camera_snapshot'),
    path('api/camera/<str:camera_id>/stream/', views.camera_stream_view, name='camera_stream_view'),

    # Camera Embed Proxy (KEY segura no backend)
    path('camera/embed/<str:camera_id>/', views.camera_embed_view, name='camera_embed'),

    # APIs - Mobile
    path('api/waze/', views.waze_data_view, name='waze_data'),
    path('api/waze-alerts/', views.waze_alerts_api, name='waze_alerts_api'),

    # APIs de Mobilidade
    path('api/transito-status/', views.api_transito_status, name='api_transito_status'),
    path('api/brt/', views.api_brt, name='api_brt'),
    path('api/metro/', views.api_metro, name='api_metro'),
    path('api/bike-rio/', views.api_bike_rio, name='api_bike_rio'),
    path('api/bolsoes/', views.api_tixxi_bolsoes, name='api_bolsoes'),

    # ============================================
    # MATRIZ DECISÓRIA - MOTOR DE DECISÃO
    # ============================================
    path('matriz/', views_matriz.matriz_dashboard, name='matriz_dashboard'),
    path('matriz/historico/', views_matriz.matriz_historico, name='matriz_historico'),
    path('matriz/estagio/<uuid:estagio_id>/', views_matriz.matriz_detalhe_estagio, name='matriz_detalhe_estagio'),

    # APIs Matriz Decisória
    path('api/matriz/calcular/', views_matriz.api_calcular_estagio, name='api_calcular_estagio'),
    path('api/matriz/ultimo/', views_matriz.api_ultimo_estagio, name='api_ultimo_estagio'),
    path('api/matriz/historico/', views_matriz.api_historico_grafico, name='api_historico_grafico'),
    path('api/matriz/estatisticas/', views_matriz.api_estatisticas, name='api_matriz_estatisticas'),

    # Manter compatibilidade com URLs antigas
    path('matriz-decisoria/', views_matriz.matriz_dashboard, name='matriz_decisoria'),

    # ============================================
    # SISTEMA DE GERENCIAMENTO DE OCORRÊNCIAS
    # ============================================
    path('ocorrencias/', views_ocorrencias.ocorrencias_dashboard, name='ocorrencias_dashboard'),
    path('ocorrencias/lista/', views_ocorrencias.ocorrencias_lista, name='ocorrencias_lista'),
    path('ocorrencias/criar/', views_ocorrencias.ocorrencia_criar, name='ocorrencia_criar'),
    path('ocorrencias/<uuid:ocorrencia_id>/', views_ocorrencias.ocorrencia_detalhe, name='ocorrencia_detalhe'),
    path('ocorrencias/<uuid:ocorrencia_id>/editar/', views_ocorrencias.ocorrencia_editar, name='ocorrencia_editar'),
    path('ocorrencias/<uuid:ocorrencia_id>/status/', views_ocorrencias.ocorrencia_atualizar_status, name='ocorrencia_atualizar_status'),
    path('ocorrencias/<uuid:ocorrencia_id>/comentario/', views_ocorrencias.ocorrencia_adicionar_comentario, name='ocorrencia_adicionar_comentario'),

    # APIs de Ocorrências
    path('api/cep/', views_ocorrencias.buscar_cep, name='api_buscar_cep'),
    path('api/ocorrencias/mapa/', views_ocorrencias.api_ocorrencias_mapa, name='api_ocorrencias_mapa'),
    path('api/ocorrencias/estatisticas/', views_ocorrencias.api_estatisticas_ocorrencias, name='api_estatisticas_ocorrencias'),
    path('api/pops/categoria/<uuid:categoria_id>/', views_ocorrencias.api_pops_por_categoria, name='api_pops_por_categoria'),

    # APIs de Agências em Ocorrências
    path('ocorrencias/<uuid:ocorrencia_id>/agencias/', views_ocorrencias.ocorrencia_adicionar_agencia, name='ocorrencia_adicionar_agencia'),
    path('ocorrencias/<uuid:ocorrencia_id>/agencias/<uuid:acionamento_id>/', views_ocorrencias.ocorrencia_atualizar_agencia, name='ocorrencia_atualizar_agencia'),
    path('ocorrencias/<uuid:ocorrencia_id>/agencias/<uuid:acionamento_id>/remover/', views_ocorrencias.ocorrencia_remover_agencia, name='ocorrencia_remover_agencia'),
    path('api/ocorrencias/<uuid:ocorrencia_id>/agencias-disponiveis/', views_ocorrencias.api_agencias_disponiveis, name='api_agencias_disponiveis'),

    # ============================================
    # SISTEMA DE ÁREAS DE OBSERVAÇÃO
    # ============================================
    path('areas/', views_areas.areas_dashboard, name='areas_dashboard'),
    path('areas/<uuid:area_id>/', views_areas.area_detalhe, name='area_detalhe'),

    # APIs de Áreas de Observação
    path('api/areas/listar/', views_areas.api_listar_areas, name='api_listar_areas'),
    path('api/areas/criar/', views_areas.api_criar_area, name='api_criar_area'),
    path('api/areas/<uuid:area_id>/atualizar/', views_areas.api_atualizar_area, name='api_atualizar_area'),
    path('api/areas/<uuid:area_id>/deletar/', views_areas.api_deletar_area, name='api_deletar_area'),
    path('api/areas/<uuid:area_id>/inventariar/', views_areas.api_inventariar_area, name='api_inventariar_area'),
    path('api/areas/<uuid:area_id>/alertas/', views_areas.api_alertas_area, name='api_alertas_area'),
    path('api/areas/alertas/<uuid:alerta_id>/lido/', views_areas.api_marcar_alerta_lido, name='api_marcar_alerta_lido'),

    # Exportação de Áreas
    path('api/areas/<uuid:area_id>/exportar/geojson/', views_areas.api_exportar_geojson, name='api_exportar_geojson'),
    path('api/areas/<uuid:area_id>/exportar/kml/', views_areas.api_exportar_kml, name='api_exportar_kml'),
    path('api/areas/<uuid:area_id>/exportar/pdf/', views_areas.api_exportar_relatorio_pdf, name='api_exportar_pdf'),

    # Importação de KML/KMZ
    path('api/areas/importar-kml/', views_areas.api_importar_kml, name='api_importar_kml'),

    # Gerenciamento de Áreas Importadas
    path('api/areas/importacoes/', views_areas.api_listar_importacoes, name='api_listar_importacoes'),
    path('api/areas/<uuid:area_id>/excluir/', views_areas.api_excluir_area, name='api_excluir_area'),
    path('api/areas/<uuid:area_id>/toggle-ativa/', views_areas.api_toggle_area_ativa, name='api_toggle_area_ativa'),
    path('api/areas/grupo/<str:grupo_id>/excluir/', views_areas.api_excluir_grupo_importacao, name='api_excluir_grupo'),
    path('api/areas/grupo/<str:grupo_id>/agendamento/', views_areas.api_atualizar_agendamento_grupo, name='api_atualizar_agendamento_grupo'),
    path('api/areas/excluir-todas/', views_areas.api_excluir_todas_areas, name='api_excluir_todas_areas'),

    # APIs de Alertas Confirmados pelo Usuário (persistência no servidor)
    path('api/alertas-confirmados/', views_areas.api_alertas_confirmados_listar, name='api_alertas_confirmados_listar'),
    path('api/alertas-confirmados/salvar/', views_areas.api_alertas_confirmados_salvar, name='api_alertas_confirmados_salvar'),
    path('api/alertas-confirmados/salvar-lote/', views_areas.api_alertas_confirmados_salvar_lote, name='api_alertas_confirmados_salvar_lote'),
]

# Servir arquivos estáticos em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)