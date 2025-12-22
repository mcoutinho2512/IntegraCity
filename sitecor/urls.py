from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from aplicativo import views
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse


# REDIRECIONAMENTO FORÇADO PARA LOGIN
def redirecionar_para_login(request):
    from django.shortcuts import redirect
    return redirect('/login/')

urlpatterns = [
    path('', include('aplicativo.urls')),
    path('admin/', admin.site.urls),
    path('video/', views.video_dashboard, name='video_dashboard'),
    path('api/cameras-proxy/', views.api_cameras_proxy, name='cameras_proxy'),
    path('', redirecionar_para_login),
    path('waze-dashboard/', views.waze_dashboard_view, name='waze_dashboard'),
    path('cor/', views.cor_dashboard_view, name='cor_dashboard'),
    
    # APIs que funcionam
    path('api/sirenes/', views.sirene_api, name='api_sirenes'),
    path('api/pluviometros/', views.pluviometros_view, name='api_pluviometros'),
    path('api/calor/', views.calor_api, name='api_calor'),
    
    # API do Estagio
    path('api/estagio-externo/', views.estagio_proxy, name='estagio_proxy'),
    path('api/estagio/', views.api_estagio, name='api_estagio'),
    path('api/estagio-atual/', views.api_estagio_atual, name='api_estagio_atual'),

    # API da Chuva e vento
    path('api/chuva/', views.chuva_api, name='api_chuva'),
    path('api/ventos/', views.estacoes_vento_view, name='api_ventos'),

    path('api/alertas/', views.alertas_api, name='api_alertas'),
    path('api/bens-tombados/', views.bens_tombados_view, name='api_bens_tombados'),
    path('api/escolas/', views.escolas_view, name='api_escolas'),
    path('api/eventos/', views.api_eventos, name='api_eventos'),
    path('api/ocorrencias/', views.api_ocorrencias, name='api_ocorrencias'),
    path('api/hospitais/', views.api_hospitais, name='api_hospitais'),
    path('api/cameras/', views.api_cameras, name='api_cameras'),

     # ========================================
    # 🎥 APIs DE SNAPSHOT/STREAMING DE CÂMERAS
    # ========================================
    path('api/camera/<str:camera_id>/snapshot/', views.camera_snapshot, name='camera_snapshot'),
    path('api/camera/<str:camera_id>/info/', views.camera_stream_info, name='camera_info'),
    path('api/cameras/status/', views.cameras_status, name='cameras_status'),
    path('hls/<str:camera_id>/playlist.m3u8', views.camera_hls_placeholder, name='hls_placeholder'),

    path('api/camera/<str:camera_id>/stream/', views.camera_stream_view, name='camera_stream'),
   
    path('api/waze/', views.waze_data_view, name='waze_data'),
    
    # Meteorologia
    path('meteorologia/', views.meteorologia_dashboard_view, name='meteorologia_dashboard'),
    path('api/previsao/', views.api_previsao_tempo, name='api_previsao'),
    path('api/historico-chuva/', views.api_historico_chuva, name='api_historico_chuva'),
    path('api/alertas-meteorologicos/', views.api_alertas_meteorologicos, name='api_alertas_met'),
    
    # Mobilidade Urbana
    path('mobilidade/', views.mobilidade_dashboard_view, name='mobilidade_dashboard'),
    path('api/brt/', views.api_brt_linhas, name='api_brt'),
    path('api/metro/', views.api_metro_linhas, name='api_metro'),
    path('api/bike-rio/', views.api_bike_rio, name='api_bike_rio'),
    path('api/transito-status/', views.api_transito_status, name='api_transito_status'),
    
    # Video Monitoramento ← ADICIONE AQUI
    path('videomonitoramento/', views.videomonitoramento, name='videomonitoramento'),
    path('api/cameras-local/', views.cameras_api_local, name='cameras_api_local'),
    
    path('teste/', views.teste_sem_login, name='teste'),
    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
