"""
Servico de integracao com a API CSI (Coeficiente de Severidade de Impacto)
API: https://35.199.126.236:8001/Hxgn.CSIAPI/

Sistema de cache implementado para resposta instantanea.
Os dados sao atualizados em background a cada 5 minutos.
"""
import requests
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)

# Configuracoes da API CSI
CSI_API_BASE_URL = "https://35.199.126.236:8001/Hxgn.CSIAPI/api"
CSI_API_USERNAME = "RestAPI"
CSI_API_PASSWORD = "@Hexagon2024"

# Cache do token
_token_cache = {
    'token': None,
    'expires_at': None
}

# Cache dos dados CSI (resposta instantanea)
_csi_data_cache = {
    'data': None,
    'last_update': None,
    'updating': False
}

# Intervalo de atualizacao do cache (1 minuto)
CSI_CACHE_TTL = 60  # segundos


def get_csi_token():
    """Obtem token de autenticacao da API CSI"""
    global _token_cache

    # Verifica se token ainda e valido (com margem de 5 minutos)
    if _token_cache['token'] and _token_cache['expires_at']:
        if datetime.now() < _token_cache['expires_at'] - timedelta(minutes=5):
            return _token_cache['token']

    try:
        response = requests.post(
            f"{CSI_API_BASE_URL}/Login",
            json={
                "userName": CSI_API_USERNAME,
                "password": CSI_API_PASSWORD
            },
            headers={"Content-Type": "application/json"},
            verify=False,  # SSL autoassinado
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get('accessToken')
            expires_in = data.get('expiresIn', 3600)

            _token_cache['token'] = token
            _token_cache['expires_at'] = datetime.now() + timedelta(seconds=expires_in)

            logger.info("Token CSI obtido com sucesso")
            return token
        else:
            logger.error(f"Erro ao obter token CSI: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Excecao ao obter token CSI: {str(e)}")
        return None


def _parse_top5_values(json_str, name_field='Bairro'):
    """Parseia os valores Top5 e normaliza para formato padrao"""
    try:
        items = json.loads(json_str)
        result = []
        for item in items:
            result.append({
                name_field: item.get('key', ''),
                'Valor': item.get('value', 0)
            })
        return result
    except:
        return []


def get_csi_top5():
    """Obtem os Top 5 indicadores de severidade"""
    token = get_csi_token()
    if not token:
        return None

    try:
        response = requests.get(
            f"{CSI_API_BASE_URL}/Top/GetTop5",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            verify=False,
            timeout=60  # Aumentado para 60 segundos
        )

        if response.status_code == 200:
            # A resposta pode vir com dois JSONs concatenados
            text = response.text

            # Encontrar onde termina o primeiro JSON
            brace_count = 0
            split_index = len(text)
            for i, char in enumerate(text):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        split_index = i + 1
                        break

            # Parsear o primeiro JSON (indicadores)
            indicadores_json = text[:split_index]
            indicadores = json.loads(indicadores_json)

            # Processar dados
            result = {
                'coeficientes': {},
                'bairros_severidade': [],
                'zonas_severidade': [],
                'bairros_ocorrencia': [],
                'bairros_transito': [],
                'zonas_ocorrencia': [],
                'zonas_transito': [],
            }

            # Extrair Top 5 Bairros por Severidade
            if 'BairroSeveridadedeImpacto' in indicadores:
                top5_str = indicadores['BairroSeveridadedeImpacto']['TopIndicadores']['Top5Valores']
                result['bairros_severidade'] = _parse_top5_values(top5_str, 'Bairro')

            # Extrair Top 5 Zonas por Severidade
            if 'ZonaSeveridadedeImpacto' in indicadores:
                top5_str = indicadores['ZonaSeveridadedeImpacto']['TopIndicadores']['Top5Valores']
                result['zonas_severidade'] = _parse_top5_values(top5_str, 'Zona')

            # Extrair Top 5 Bairros por Ocorrencia
            if 'BairroOcorrencia' in indicadores:
                top5_str = indicadores['BairroOcorrencia']['TopIndicadores']['Top5Valores']
                result['bairros_ocorrencia'] = _parse_top5_values(top5_str, 'Bairro')

            # Extrair Top 5 Bairros por Transito
            if 'BairroTransito' in indicadores:
                top5_str = indicadores['BairroTransito']['TopIndicadores']['Top5Valores']
                result['bairros_transito'] = _parse_top5_values(top5_str, 'Bairro')

            # Extrair Top 5 Zonas por Ocorrencia
            if 'ZonaOcorrencia' in indicadores:
                top5_str = indicadores['ZonaOcorrencia']['TopIndicadores']['Top5Valores']
                result['zonas_ocorrencia'] = _parse_top5_values(top5_str, 'Zona')

            # Extrair Top 5 Zonas por Transito
            if 'ZonaTransito' in indicadores:
                top5_str = indicadores['ZonaTransito']['TopIndicadores']['Top5Valores']
                result['zonas_transito'] = _parse_top5_values(top5_str, 'Zona')

            logger.info("Dados CSI obtidos com sucesso")
            return result

        else:
            logger.error(f"Erro ao obter CSI Top5: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Excecao ao obter CSI Top5: {str(e)}")
        return None


def get_csi_zonas():
    """Obtem lista de zonas"""
    token = get_csi_token()
    if not token:
        return None

    try:
        response = requests.get(
            f"{CSI_API_BASE_URL}/Zona/GetZonas",
            headers={"Authorization": f"Bearer {token}"},
            verify=False,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        return None

    except Exception as e:
        logger.error(f"Erro ao obter zonas CSI: {str(e)}")
        return None


def get_csi_bairros():
    """Obtem lista de bairros"""
    token = get_csi_token()
    if not token:
        return None

    try:
        response = requests.get(
            f"{CSI_API_BASE_URL}/Bairro/GetBairros",
            headers={"Authorization": f"Bearer {token}"},
            verify=False,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        return None

    except Exception as e:
        logger.error(f"Erro ao obter bairros CSI: {str(e)}")
        return None


# Desabilitar warnings de SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================
# SISTEMA DE CACHE COM ATUALIZACAO EM BACKGROUND
# ============================================

def _update_cache():
    """Atualiza o cache com dados frescos da API"""
    global _csi_data_cache

    if _csi_data_cache['updating']:
        return  # Ja esta atualizando

    _csi_data_cache['updating'] = True
    try:
        data = get_csi_top5()
        if data:
            _csi_data_cache['data'] = data
            _csi_data_cache['last_update'] = datetime.now()
            logger.info("Cache CSI atualizado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao atualizar cache CSI: {str(e)}")
    finally:
        _csi_data_cache['updating'] = False


def _update_cache_background():
    """Atualiza o cache em uma thread separada"""
    thread = threading.Thread(target=_update_cache, daemon=True)
    thread.start()


def get_csi_top5_cached():
    """
    Retorna dados CSI do cache (resposta instantanea).
    Se o cache estiver vazio ou expirado, dispara atualizacao em background.
    """
    global _csi_data_cache

    now = datetime.now()

    # Verificar se cache precisa ser atualizado
    cache_expired = False
    if _csi_data_cache['last_update']:
        age = (now - _csi_data_cache['last_update']).total_seconds()
        cache_expired = age > CSI_CACHE_TTL

    # Se cache vazio, busca sincrono (primeira vez)
    if _csi_data_cache['data'] is None:
        logger.info("Cache CSI vazio, buscando dados...")
        _update_cache()

    # Se cache expirado, dispara atualizacao em background
    elif cache_expired and not _csi_data_cache['updating']:
        logger.info("Cache CSI expirado, atualizando em background...")
        _update_cache_background()

    # Retorna dados do cache (mesmo que estejam sendo atualizados)
    return _csi_data_cache['data']


def get_csi_cache_status():
    """Retorna informacoes sobre o status do cache"""
    global _csi_data_cache

    status = {
        'has_data': _csi_data_cache['data'] is not None,
        'last_update': None,
        'age_seconds': None,
        'updating': _csi_data_cache['updating'],
        'ttl_seconds': CSI_CACHE_TTL
    }

    if _csi_data_cache['last_update']:
        status['last_update'] = _csi_data_cache['last_update'].isoformat()
        status['age_seconds'] = (datetime.now() - _csi_data_cache['last_update']).total_seconds()

    return status


def force_cache_refresh():
    """Forca atualizacao imediata do cache"""
    global _csi_data_cache
    _csi_data_cache['last_update'] = None  # Invalida cache
    _update_cache_background()
    return True


# Thread de atualizacao periodica
_background_updater_running = False

def _background_updater_loop():
    """Loop que atualiza o cache periodicamente"""
    global _background_updater_running

    logger.info("Iniciando atualizador CSI em background...")

    # Primeira atualizacao imediata
    _update_cache()

    while _background_updater_running:
        time.sleep(CSI_CACHE_TTL)
        if _background_updater_running:
            _update_cache()


def start_csi_background_updater():
    """Inicia o atualizador em background (chamar no startup da aplicacao)"""
    global _background_updater_running

    if _background_updater_running:
        return False  # Ja esta rodando

    _background_updater_running = True
    thread = threading.Thread(target=_background_updater_loop, daemon=True)
    thread.start()
    logger.info("Atualizador CSI em background iniciado")
    return True


def stop_csi_background_updater():
    """Para o atualizador em background"""
    global _background_updater_running
    _background_updater_running = False
    logger.info("Atualizador CSI em background parado")
