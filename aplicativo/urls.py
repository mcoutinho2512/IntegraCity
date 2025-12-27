from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from aplicativo import views

urlpatterns = [
    # LOGIN - PÁGINA PRINCIPAL
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

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

    # Matriz Decisória
    path('matriz-decisoria/', views.matriz_decisoria, name='matriz_decisoria'),
    path('api/matriz-decisoria/', views.api_matriz_decisoria, name='api_matriz_decisoria'),
]

# Servir arquivos estáticos em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
