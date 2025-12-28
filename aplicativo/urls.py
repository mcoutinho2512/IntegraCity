from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from aplicativo import views
from aplicativo import views_users
from aplicativo import views_ocorrencias
from aplicativo import views_matriz

urlpatterns = [
    # LOGIN - PÁGINA PRINCIPAL
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # ============================================
    # GERENCIAMENTO DE USUÁRIOS
    # ============================================
    path('users/', views_users.user_management, name='user_management'),
    path('users/create/', views_users.user_create, name='user_create'),
    path('users/<int:user_id>/', views_users.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views_users.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views_users.user_delete, name='user_delete'),
    path('users/<int:user_id>/toggle/', views_users.user_toggle_status, name='user_toggle_status'),
    path('users/<int:user_id>/unlock/', views_users.user_unlock, name='user_unlock'),
    path('users/<int:user_id>/reset-password/', views_users.user_reset_password, name='user_reset_password'),
    path('users/<int:user_id>/permissions/', views_users.user_permissions, name='user_permissions'),

    # APIs de Usuários
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

    path('mobilidade/', views.mobilidade_dashboard_view, name='mobilidade_dashboard'),
    path('meteorologia/', views.meteorologia_dashboard_view, name='meteorologia_dashboard'),

    # APIs - Sirenes
    path('api/sirenes/', views.sirene_api, name='sirene_api'),
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

    # APIs - Locais
    path('api/escolas/', views.escolas_view, name='escolas'),
    path('api/hospitais/', views.api_hospitais, name='api_hospitais'),
    path('api/pluviometros/', views.api_pluviometros, name='pluviometros'),
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

    # APIs - Mobile
    path('api/waze/', views.waze_data_view, name='waze_data'),
    path('api/waze-alerts/', views.waze_alerts_api, name='waze_alerts_api'),

    # APIs de Mobilidade
    path('api/transito-status/', views.api_transito_status, name='api_transito_status'),
    path('api/brt/', views.api_brt, name='api_brt'),
    path('api/metro/', views.api_metro, name='api_metro'),
    path('api/bike-rio/', views.api_bike_rio, name='api_bike_rio'),

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
]

# Servir arquivos estáticos em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
