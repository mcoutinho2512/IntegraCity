"""
Integrador Meteorológico Multi-Fonte
====================================

Coleta dados meteorológicos em tempo real para alimentar o
Grupo 1 (Meteorologia) do Motor de Decisão.

Fontes de Dados:
1. Open-Meteo (primária) - API gratuita e confiável
   - https://open-meteo.com/en/docs
   - Não requer API key
   - Dados atualizados a cada hora
   - Cobertura global

2. INMET (cadastro de estações)
   - https://apitempo.inmet.gov.br
   - Lista de estações brasileiras
   - Usada para referência geográfica
"""

import requests
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from django.utils import timezone
from django.db import transaction
import logging
from math import radians, sin, cos, sqrt, atan2

logger = logging.getLogger(__name__)


class IntegradorINMET:
    """
    Integrador Meteorológico Multi-Fonte

    Responsável por:
    - Buscar estações próximas a uma cidade (INMET)
    - Coletar dados meteorológicos em tempo real (Open-Meteo)
    - Calcular nível do Grupo 1 (Meteorologia)
    """

    BASE_URL_INMET = "https://apitempo.inmet.gov.br"
    BASE_URL_OPENMETEO = "https://api.open-meteo.com/v1"
    TIMEOUT = 15  # segundos

    # Limiares para cálculo do nível meteorológico (padrão COR Rio)
    # https://cor.rio/estagios-operacionais-da-cidade/
    LIMIARES_CHUVA = {
        5: 30,   # E5 (Crise): >= 30mm/h
        4: 20,   # E4 (Alerta): >= 20mm/h
        3: 10,   # E3 (Atenção): >= 10mm/h
        2: 5,    # E2 (Mobilização): >= 5mm/h
    }

    LIMIARES_VENTO = {
        5: 90,   # E5 (Crise): >= 90km/h (vendaval)
        4: 70,   # E4 (Alerta): >= 70km/h
        3: 50,   # E3 (Atenção): >= 50km/h
        2: 40,   # E2 (Mobilização): >= 40km/h
    }

    # Limiares para Níveis de Calor (NC1-NC5) - Protocolo COR Rio
    # Baseado no Índice de Calor (Heat Index)
    # https://cor.rio/niveis-de-calor/
    LIMIARES_CALOR = {
        # NC5 (Crise): IC > 44°C por 2h+
        5: {'ic_min': 44, 'horas_min': 2},
        # NC4 (Alerta): IC 40-44°C por 2h+
        4: {'ic_min': 40, 'ic_max': 44, 'horas_min': 2},
        # NC3 (Atenção): IC 36-40°C por 6h+ (persistente)
        3: {'ic_min': 36, 'ic_max': 40, 'horas_min': 6},
        # NC2 (Mobilização): IC 36-40°C por 4h+
        2: {'ic_min': 36, 'ic_max': 40, 'horas_min': 4},
        # NC1 (Normal): IC < 36°C
        1: {'ic_max': 36, 'horas_min': 0},
    }

    def __init__(self, cliente):
        """
        Inicializa o integrador com um cliente específico

        Args:
            cliente: Instância do modelo Cliente
        """
        self.cliente = cliente

    def buscar_estacoes_proximas(self, raio_km: int = 100) -> List[Dict]:
        """
        Busca estações INMET próximas à cidade do cliente

        Args:
            raio_km: Raio de busca em quilômetros (padrão 100km)

        Returns:
            Lista de dicionários com dados das estações, ordenada por distância
        """
        try:
            logger.info(f"Buscando estações INMET próximas a {self.cliente.nome} (raio {raio_km}km)")

            # Buscar todas as estações automáticas (tipo T)
            response = requests.get(
                f"{self.BASE_URL_INMET}/estacoes/T",
                timeout=self.TIMEOUT
            )
            response.raise_for_status()

            todas_estacoes = response.json()
            logger.info(f"Total de estações INMET disponíveis: {len(todas_estacoes)}")

            estacoes_proximas = []

            lat_cliente = float(self.cliente.latitude)
            lon_cliente = float(self.cliente.longitude)

            for estacao in todas_estacoes:
                try:
                    lat_estacao = float(estacao.get('VL_LATITUDE', 0))
                    lon_estacao = float(estacao.get('VL_LONGITUDE', 0))

                    # Calcular distância usando Haversine
                    distancia = self._calcular_distancia(
                        lat_cliente, lon_cliente,
                        lat_estacao, lon_estacao
                    )

                    if distancia <= raio_km:
                        estacoes_proximas.append({
                            'codigo': estacao.get('CD_ESTACAO'),
                            'nome': estacao.get('DC_NOME'),
                            'tipo': 'automatica',
                            'uf': estacao.get('SG_ESTADO'),
                            'latitude': lat_estacao,
                            'longitude': lon_estacao,
                            'altitude': float(estacao.get('VL_ALTITUDE', 0)),
                            'distancia': round(distancia, 2),
                            'situacao': estacao.get('CD_SITUACAO'),
                        })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Erro ao processar estação {estacao.get('CD_ESTACAO')}: {e}")
                    continue

            # Ordenar por distância (mais próxima primeiro)
            estacoes_proximas.sort(key=lambda x: x['distancia'])

            logger.info(f"Encontradas {len(estacoes_proximas)} estações no raio de {raio_km}km")

            return estacoes_proximas

        except requests.RequestException as e:
            logger.error(f"Erro HTTP ao buscar estações INMET: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar estações: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _calcular_distancia(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula distância entre dois pontos usando fórmula Haversine

        Args:
            lat1, lon1: Coordenadas do primeiro ponto
            lat2, lon2: Coordenadas do segundo ponto

        Returns:
            Distância em quilômetros
        """
        R = 6371  # Raio da Terra em km

        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)

        a = (sin(dlat/2)**2 +
             cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2)
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def cadastrar_estacoes(self, raio_km: int = 100, max_estacoes: int = 5) -> int:
        """
        Busca e cadastra estações próximas ao cliente

        Args:
            raio_km: Raio de busca em quilômetros
            max_estacoes: Máximo de estações a cadastrar

        Returns:
            Número de estações cadastradas
        """
        from ..models import EstacaoMeteorologica

        estacoes = self.buscar_estacoes_proximas(raio_km)

        if not estacoes:
            logger.warning(f"Nenhuma estação encontrada para {self.cliente.nome}")
            return 0

        cadastradas = 0

        with transaction.atomic():
            for i, est in enumerate(estacoes[:max_estacoes]):
                obj, created = EstacaoMeteorologica.objects.update_or_create(
                    codigo_inmet=est['codigo'],
                    defaults={
                        'cliente': self.cliente,
                        'nome': est['nome'],
                        'tipo': est['tipo'],
                        'latitude': est['latitude'],
                        'longitude': est['longitude'],
                        'altitude': est['altitude'],
                        'distancia_km': est['distancia'],
                        'principal': (i == 0),  # Primeira é principal
                        'ativa': True,
                    }
                )

                if created:
                    cadastradas += 1
                    logger.info(f"Estação cadastrada: {obj.nome} ({obj.distancia_km}km)")
                else:
                    logger.info(f"Estação atualizada: {obj.nome} ({obj.distancia_km}km)")

        return cadastradas

    def coletar_dados_openmeteo(self, latitude: float = None, longitude: float = None) -> Optional[object]:
        """
        Coleta dados meteorológicos em tempo real da API Open-Meteo

        Args:
            latitude: Latitude (usa do cliente se não informada)
            longitude: Longitude (usa do cliente se não informada)

        Returns:
            Objeto DadosMeteorologicos criado ou None em caso de erro
        """
        from ..models import DadosMeteorologicos, EstacaoMeteorologica

        lat = latitude or float(self.cliente.latitude)
        lon = longitude or float(self.cliente.longitude)

        try:
            logger.info(f"Coletando dados Open-Meteo para {self.cliente.nome} ({lat}, {lon})")

            # Parâmetros da requisição Open-Meteo
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m,wind_gusts_10m,wind_direction_10m,pressure_msl',
                'timezone': 'America/Sao_Paulo',
            }

            response = requests.get(
                f"{self.BASE_URL_OPENMETEO}/forecast",
                params=params,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()

            dados_api = response.json()

            if not dados_api or 'current' not in dados_api:
                logger.warning(f"Sem dados Open-Meteo para {self.cliente.nome}")
                return None

            current = dados_api['current']

            # Parsear data/hora (formato ISO: "2025-12-28T16:15")
            data_hora_str = current.get('time')
            if not data_hora_str:
                logger.error("Sem timestamp nos dados Open-Meteo")
                return None

            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
            data_hora = timezone.make_aware(data_hora, timezone.get_current_timezone())

            # Buscar ou criar estação virtual para Open-Meteo
            estacao, est_created = EstacaoMeteorologica.objects.get_or_create(
                codigo_inmet=f"OPENMETEO_{self.cliente.slug.upper()}",
                defaults={
                    'cliente': self.cliente,
                    'nome': f"Open-Meteo - {self.cliente.cidade}",
                    'tipo': 'automatica',
                    'latitude': lat,
                    'longitude': lon,
                    'altitude': dados_api.get('elevation', 0),
                    'distancia_km': 0,
                    'principal': True,
                    'ativa': True,
                }
            )

            if est_created:
                logger.info(f"Estação virtual criada: {estacao.nome}")
                # Desmarcar outras estações como principal
                EstacaoMeteorologica.objects.filter(
                    cliente=self.cliente
                ).exclude(id=estacao.id).update(principal=False)

            # Criar ou atualizar registro
            dados_obj, created = DadosMeteorologicos.objects.update_or_create(
                estacao=estacao,
                data_hora=data_hora,
                defaults={
                    'temperatura': self._safe_decimal(current.get('temperature_2m')),
                    'temperatura_max': None,
                    'temperatura_min': None,
                    'umidade': self._safe_decimal(current.get('relative_humidity_2m')),
                    'pressao': self._safe_decimal(current.get('pressure_msl')),
                    'precipitacao_horaria': self._safe_decimal(current.get('precipitation') or current.get('rain')),
                    'vento_velocidade': self._safe_decimal(current.get('wind_speed_10m')),
                    'vento_direcao': self._safe_decimal(current.get('wind_direction_10m')),
                    'vento_rajada': self._safe_decimal(current.get('wind_gusts_10m')),
                    'radiacao': None,
                    'ponto_orvalho': None,
                    'dados_raw': dados_api,
                }
            )

            acao = "criado" if created else "atualizado"
            logger.info(f"Dado Open-Meteo {acao}: {estacao.nome} - {data_hora}")

            return dados_obj

        except requests.RequestException as e:
            logger.error(f"Erro HTTP ao coletar dados Open-Meteo: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao coletar dados Open-Meteo: {e}")
            import traceback
            traceback.print_exc()
            return None

    def coletar_dados_tempo_real(self, estacao) -> Optional[object]:
        """
        Coleta dados meteorológicos em tempo real

        Usa Open-Meteo como fonte primária, que funciona para qualquer localização.
        Os dados são salvos associados à estação mais próxima para referência.

        Args:
            estacao: Objeto EstacaoMeteorologica

        Returns:
            Objeto DadosMeteorologicos criado ou None em caso de erro
        """
        # Usar Open-Meteo com as coordenadas da estação
        return self.coletar_dados_openmeteo(
            latitude=float(estacao.latitude),
            longitude=float(estacao.longitude)
        )

    def coletar_todas_estacoes(self) -> Tuple[int, int]:
        """
        Coleta dados meteorológicos do cliente via Open-Meteo

        Prioriza coleta central (coordenadas do cliente) e opcionalmente
        coleta de estações adicionais se configuradas.

        Returns:
            Tupla (sucesso, total)
        """
        from ..models import EstacaoMeteorologica

        sucesso = 0
        total = 1  # Pelo menos a coleta principal

        # Coleta principal usando coordenadas do cliente
        if self.coletar_dados_openmeteo():
            sucesso += 1
            logger.info(f"Coleta Open-Meteo OK para {self.cliente.nome}")
        else:
            logger.warning(f"Falha na coleta Open-Meteo para {self.cliente.nome}")

        # Opcionalmente coletar de estações INMET adicionais (não principais)
        estacoes_extras = EstacaoMeteorologica.objects.filter(
            cliente=self.cliente,
            ativa=True,
            principal=False
        ).exclude(codigo_inmet__startswith='OPENMETEO_')

        total += estacoes_extras.count()

        for estacao in estacoes_extras:
            if self.coletar_dados_tempo_real(estacao):
                sucesso += 1

        logger.info(f"Coleta finalizada para {self.cliente.nome}: {sucesso}/{total}")

        return sucesso, total

    def _safe_decimal(self, value) -> Optional[Decimal]:
        """Converte valor para Decimal com segurança"""
        if value is None or value == '' or value == '-' or value == 'null':
            return None
        try:
            # Substituir vírgula por ponto
            valor_str = str(value).replace(',', '.').strip()
            if not valor_str or valor_str in ['-', 'null', 'None']:
                return None
            return Decimal(valor_str)
        except (ValueError, TypeError):
            return None

    def _calcular_heat_index(self, temp_c: float, umidade_percent: float) -> float:
        """
        Calcula o Índice de Calor (Heat Index) usando fórmula NOAA simplificada

        O Heat Index representa a temperatura "sentida" pelo corpo humano,
        considerando a combinação de temperatura e umidade relativa do ar.

        Args:
            temp_c: Temperatura em Celsius
            umidade_percent: Umidade relativa em porcentagem (0-100)

        Returns:
            Índice de Calor em Celsius
        """
        # Abaixo de 27°C, o Heat Index é aproximadamente igual à temperatura
        if temp_c < 27:
            return temp_c

        # Converter para Fahrenheit (fórmula NOAA usa Fahrenheit)
        temp_f = (temp_c * 9/5) + 32
        rh = umidade_percent

        # Rothfusz regression equation (NOAA)
        # https://www.weather.gov/media/ffc/ta_htindx.PDF
        hi = (-42.379 +
              2.04901523 * temp_f +
              10.14333127 * rh -
              0.22475541 * temp_f * rh -
              6.83783e-3 * temp_f**2 -
              5.481717e-2 * rh**2 +
              1.22874e-3 * temp_f**2 * rh +
              8.5282e-4 * temp_f * rh**2 -
              1.99e-6 * temp_f**2 * rh**2)

        # Ajustes para condições específicas
        if rh < 13 and 80 <= temp_f <= 112:
            # Ajuste para baixa umidade
            adjustment = ((13 - rh) / 4) * ((17 - abs(temp_f - 95)) / 17) ** 0.5
            hi -= adjustment
        elif rh > 85 and 80 <= temp_f <= 87:
            # Ajuste para alta umidade
            adjustment = ((rh - 85) / 10) * ((87 - temp_f) / 5)
            hi += adjustment

        # Converter de volta para Celsius
        return (hi - 32) * 5/9

    def calcular_nivel_calor(self) -> Tuple[int, Dict]:
        """
        Calcula o Nível de Calor (NC1-NC5) baseado no Índice de Calor

        Protocolo COR Rio para ondas de calor (padronizado com estágios E1-E5):
        - NC1 (Normal): IC < 36°C
        - NC2 (Mobilização): IC 36-40°C por 4h+
        - NC3 (Atenção): IC 36-40°C por 6h+ (persistente)
        - NC4 (Alerta): IC 40-44°C por 2h+
        - NC5 (Crise): IC > 44°C por 2h+

        Returns:
            Tupla (nivel_nc, detalhes_dict)
        """
        from ..models import EstacaoMeteorologica, DadosMeteorologicos

        # Buscar estação principal
        estacao = EstacaoMeteorologica.objects.filter(
            cliente=self.cliente,
            principal=True,
            ativa=True
        ).first()

        if not estacao:
            logger.warning(f"Nenhuma estação configurada para cálculo de calor - {self.cliente.nome}")
            return 1, {
                'nivel': 1,
                'nomenclatura': 'Normal',
                'erro': 'Nenhuma estação meteorológica configurada',
                'razao': 'Configure estações para monitoramento de calor'
            }

        # Buscar dados das últimas 6 horas para análise de persistência
        limite = timezone.now() - timedelta(hours=6)
        dados_periodo = DadosMeteorologicos.objects.filter(
            estacao=estacao,
            data_hora__gte=limite,
            temperatura__isnull=False,
            umidade__isnull=False
        ).order_by('-data_hora')

        if not dados_periodo.exists():
            logger.warning(f"Sem dados de temperatura/umidade para {estacao.nome}")
            return 1, {
                'nivel': 1,
                'nomenclatura': 'Normal',
                'erro': 'Sem dados de temperatura/umidade recentes',
                'razao': 'Aguardando coleta de dados meteorológicos',
                'estacao': estacao.nome,
            }

        # Calcular Heat Index para cada ponto de dados
        indices_calor = []
        for dado in dados_periodo:
            temp = float(dado.temperatura)
            umid = float(dado.umidade)

            ic = self._calcular_heat_index(temp, umid)
            indices_calor.append({
                'data_hora': dado.data_hora.isoformat(),
                'temperatura': round(temp, 1),
                'umidade': round(umid, 1),
                'heat_index': round(ic, 1)
            })

        if not indices_calor:
            return 1, {
                'nivel': 1,
                'nomenclatura': 'Normal',
                'erro': 'Não foi possível calcular índices de calor',
                'razao': 'Dados insuficientes'
            }

        # Estatísticas gerais
        ic_valores = [x['heat_index'] for x in indices_calor]
        ic_max = max(ic_valores)
        ic_medio = sum(ic_valores) / len(ic_valores)
        temp_max = max([x['temperatura'] for x in indices_calor])
        temp_media = sum([x['temperatura'] for x in indices_calor]) / len(indices_calor)
        umid_media = sum([x['umidade'] for x in indices_calor]) / len(indices_calor)

        # Contar quantos registros em cada faixa de IC
        # Cada registro representa aproximadamente 1 hora (coleta horária Open-Meteo)
        horas_36_40 = sum(1 for ic in ic_valores if 36 <= ic < 40)
        horas_40_44 = sum(1 for ic in ic_valores if 40 <= ic < 44)
        horas_acima_44 = sum(1 for ic in ic_valores if ic >= 44)

        # Determinar nível de calor (NC1-NC5, padronizado com E1-E5)
        nivel_nc = 1  # Normal por padrão
        razao = 'Condições normais de temperatura'
        nomenclatura = 'Normal'

        # Aplicar regras (do mais grave para o menos grave)
        if horas_acima_44 >= 2:
            nivel_nc = 5
            razao = f'ONDA DE CALOR EXTREMA: IC acima de 44°C por {horas_acima_44}h (máx: {ic_max:.1f}°C)'
            nomenclatura = 'Crise'
        elif horas_40_44 >= 2:
            nivel_nc = 4
            razao = f'ONDA DE CALOR: IC entre 40-44°C por {horas_40_44}h (máx: {ic_max:.1f}°C)'
            nomenclatura = 'Alerta'
        elif horas_36_40 >= 6:
            nivel_nc = 3
            razao = f'CALOR PERSISTENTE: IC entre 36-40°C por {horas_36_40}h (máx: {ic_max:.1f}°C)'
            nomenclatura = 'Atenção'
        elif horas_36_40 >= 4:
            nivel_nc = 2
            razao = f'CALOR ELEVADO: IC entre 36-40°C por {horas_36_40}h (máx: {ic_max:.1f}°C)'
            nomenclatura = 'Mobilização'
        elif ic_max >= 36:
            nivel_nc = 2
            razao = f'IC pontual elevado: {ic_max:.1f}°C (aguardando persistência)'
            nomenclatura = 'Mobilização'

        # Cores por nível (padrão COR Rio NC1-NC5)
        CORES_NC = {
            1: '#00ff88',   # Verde - Normal
            2: '#00D4FF',   # Cyan - Mobilização
            3: '#FFB800',   # Amarelo - Atenção
            4: '#FF6B00',   # Laranja - Alerta
            5: '#FF0055',   # Vermelho - Crise
        }

        detalhes = {
            'nivel': nivel_nc,
            'nomenclatura': nomenclatura,
            'cor': CORES_NC.get(nivel_nc, '#00ff88'),
            'ic_max': round(ic_max, 1),
            'ic_medio': round(ic_medio, 1),
            'temp_max': round(temp_max, 1),
            'temp_media': round(temp_media, 1),
            'umidade_media': round(umid_media, 1),
            'horas_analisadas': len(indices_calor),
            'horas_36_40': horas_36_40,
            'horas_40_44': horas_40_44,
            'horas_acima_44': horas_acima_44,
            'razao': razao,
            'estacao': estacao.nome,
            'serie_temporal': indices_calor[:12],  # Últimos 12 registros para gráfico
        }

        logger.info(f"Nível de Calor para {self.cliente.nome}: NC{nivel_nc} ({nomenclatura}) - IC máx: {ic_max:.1f}°C")

        return nivel_nc, detalhes

    def calcular_nivel_meteorologia(self) -> Tuple[int, Dict]:
        """
        Calcula nível do Grupo 1 (Meteorologia) baseado nos dados coletados

        Retorna:
            Tupla (nivel, detalhes_dict)

        Regras baseadas no padrão COR Rio:
        - E1 (Normal): Sem eventos significativos
        - E2 (Mobilização): Chuva 5-10mm/h OU vento 40-50km/h
        - E3 (Atenção): Chuva 10-20mm/h OU vento 50-70km/h
        - E4 (Alerta): Chuva 20-30mm/h OU vento 70-90km/h
        - E5 (Crise): Chuva >30mm/h OU vento >90km/h
        """
        from ..models import EstacaoMeteorologica, DadosMeteorologicos

        # Buscar estação principal
        estacao = EstacaoMeteorologica.objects.filter(
            cliente=self.cliente,
            principal=True,
            ativa=True
        ).first()

        if not estacao:
            logger.warning(f"Nenhuma estação meteorológica configurada para {self.cliente.nome}")
            return 1, {
                'erro': 'Nenhuma estação meteorológica configurada',
                'razao': 'Sistema sem dados meteorológicos - configure as estações INMET'
            }

        # Buscar dados mais recentes (últimas 3 horas de tolerância)
        limite = timezone.now() - timedelta(hours=3)
        dados_recentes = DadosMeteorologicos.objects.filter(
            estacao=estacao,
            data_hora__gte=limite
        ).order_by('-data_hora').first()

        if not dados_recentes:
            logger.warning(f"Sem dados meteorológicos recentes para {estacao.nome}")
            return 1, {
                'erro': 'Sem dados meteorológicos recentes',
                'razao': 'Última coleta há mais de 3 horas - execute a coleta',
                'estacao': estacao.nome,
                'codigo': estacao.codigo_inmet,
            }

        nivel = 1  # Normal (padrão)
        razoes = []

        # ========================================
        # CHUVA (precipitação horária)
        # ========================================
        chuva = 0
        if dados_recentes.precipitacao_horaria:
            chuva = float(dados_recentes.precipitacao_horaria)

            if chuva >= self.LIMIARES_CHUVA[5]:  # >= 30mm/h
                nivel = max(nivel, 5)
                razoes.append(f"Chuva MUITO FORTE: {chuva:.1f}mm/h (>= {self.LIMIARES_CHUVA[5]}mm)")
            elif chuva >= self.LIMIARES_CHUVA[4]:  # >= 20mm/h
                nivel = max(nivel, 4)
                razoes.append(f"Chuva FORTE: {chuva:.1f}mm/h (>= {self.LIMIARES_CHUVA[4]}mm)")
            elif chuva >= self.LIMIARES_CHUVA[3]:  # >= 10mm/h
                nivel = max(nivel, 3)
                razoes.append(f"Chuva MODERADA: {chuva:.1f}mm/h (>= {self.LIMIARES_CHUVA[3]}mm)")
            elif chuva >= self.LIMIARES_CHUVA[2]:  # >= 5mm/h
                nivel = max(nivel, 2)
                razoes.append(f"Chuva LEVE: {chuva:.1f}mm/h (>= {self.LIMIARES_CHUVA[2]}mm)")

        # ========================================
        # VENTO (usar rajada se disponível)
        # ========================================
        vento = dados_recentes.vento_rajada or dados_recentes.vento_velocidade
        vento_kmh = 0
        if vento:
            vento_kmh = float(vento)

            if vento_kmh >= self.LIMIARES_VENTO[5]:  # >= 90km/h
                nivel = max(nivel, 5)
                razoes.append(f"VENDAVAL: {vento_kmh:.1f}km/h (>= {self.LIMIARES_VENTO[5]}km/h)")
            elif vento_kmh >= self.LIMIARES_VENTO[4]:  # >= 70km/h
                nivel = max(nivel, 4)
                razoes.append(f"Vento MUITO FORTE: {vento_kmh:.1f}km/h (>= {self.LIMIARES_VENTO[4]}km/h)")
            elif vento_kmh >= self.LIMIARES_VENTO[3]:  # >= 50km/h
                nivel = max(nivel, 3)
                razoes.append(f"Vento FORTE: {vento_kmh:.1f}km/h (>= {self.LIMIARES_VENTO[3]}km/h)")
            elif vento_kmh >= self.LIMIARES_VENTO[2]:  # >= 40km/h
                nivel = max(nivel, 2)
                razoes.append(f"Vento MODERADO: {vento_kmh:.1f}km/h (>= {self.LIMIARES_VENTO[2]}km/h)")

        # ========================================
        # CALOR (Índice de Calor / Heat Index)
        # ========================================
        nivel_calor, detalhes_calor = self.calcular_nivel_calor()

        # Integrar nível de calor (NC1-NC5) no nível meteorológico (E1-E5)
        # NC corresponde diretamente ao E (NC1=E1, NC2=E2, etc.)
        if nivel_calor >= 5:
            nivel = max(nivel, 5)  # NC5 = E5 (Crise)
            razoes.append(detalhes_calor.get('razao', 'Onda de calor extrema'))
        elif nivel_calor >= 4:
            nivel = max(nivel, 4)  # NC4 = E4 (Alerta)
            razoes.append(detalhes_calor.get('razao', 'Onda de calor'))
        elif nivel_calor >= 3:
            nivel = max(nivel, 3)  # NC3 = E3 (Atenção)
            razoes.append(detalhes_calor.get('razao', 'Calor persistente'))
        elif nivel_calor >= 2:
            nivel = max(nivel, 2)  # NC2 = E2 (Mobilização)
            razoes.append(detalhes_calor.get('razao', 'Calor elevado'))
        # NC1 = Normal, não eleva o nível

        # ========================================
        # Montar detalhes
        # ========================================
        detalhes = {
            'estacao': estacao.nome,
            'codigo': estacao.codigo_inmet,
            'distancia_km': float(estacao.distancia_km),
            'data_hora': dados_recentes.data_hora.isoformat(),
            'idade_dados_minutos': dados_recentes.idade_minutos,
            'temperatura': float(dados_recentes.temperatura) if dados_recentes.temperatura else None,
            'umidade': float(dados_recentes.umidade) if dados_recentes.umidade else None,
            'pressao': float(dados_recentes.pressao) if dados_recentes.pressao else None,
            'chuva_mm_h': chuva,
            'vento_kmh': vento_kmh,
            'vento_rajada_kmh': float(dados_recentes.vento_rajada) if dados_recentes.vento_rajada else None,
            'vento_direcao': float(dados_recentes.vento_direcao) if dados_recentes.vento_direcao else None,
            'vento_direcao_cardeal': dados_recentes.vento_direcao_cardeal,
            'razao': '; '.join(razoes) if razoes else 'Condições meteorológicas normais',
            'nivel': nivel,
            # Dados de calor integrados
            'calor': detalhes_calor,
            'nivel_calor': nivel_calor,
            'heat_index': detalhes_calor.get('ic_max'),
        }

        logger.info(f"Grupo 1 (Meteorologia) para {self.cliente.nome}: Nível E{nivel} (NC{nivel_calor}) - {detalhes['razao']}")

        return nivel, detalhes

    def obter_resumo_meteorologico(self) -> Dict:
        """
        Retorna resumo dos dados meteorológicos atuais para dashboard

        Returns:
            Dicionário com resumo de todas as estações
        """
        from ..models import EstacaoMeteorologica

        estacoes = EstacaoMeteorologica.objects.filter(
            cliente=self.cliente,
            ativa=True
        ).order_by('distancia_km')

        resumo = {
            'cliente': self.cliente.nome,
            'cidade': self.cliente.cidade,
            'estado': self.cliente.estado,
            'total_estacoes': estacoes.count(),
            'estacoes': [],
            'nivel_calculado': 1,
            'detalhes_nivel': {},
        }

        for estacao in estacoes:
            ultimo_dado = estacao.get_ultimo_dado()

            estacao_info = {
                'nome': estacao.nome,
                'codigo': estacao.codigo_inmet,
                'distancia_km': float(estacao.distancia_km),
                'principal': estacao.principal,
                'dados': None,
            }

            if ultimo_dado:
                estacao_info['dados'] = {
                    'data_hora': ultimo_dado.data_hora.isoformat(),
                    'idade_minutos': ultimo_dado.idade_minutos,
                    'temperatura': float(ultimo_dado.temperatura) if ultimo_dado.temperatura else None,
                    'umidade': float(ultimo_dado.umidade) if ultimo_dado.umidade else None,
                    'chuva_mm': float(ultimo_dado.precipitacao_horaria) if ultimo_dado.precipitacao_horaria else 0,
                    'vento_kmh': float(ultimo_dado.vento_velocidade) if ultimo_dado.vento_velocidade else 0,
                    'vento_rajada': float(ultimo_dado.vento_rajada) if ultimo_dado.vento_rajada else None,
                }

            resumo['estacoes'].append(estacao_info)

        # Calcular nível
        nivel, detalhes = self.calcular_nivel_meteorologia()
        resumo['nivel_calculado'] = nivel
        resumo['detalhes_nivel'] = detalhes

        return resumo

    def obter_dados_atuais_openmeteo(self) -> Optional[Dict]:
        """
        Obtém dados meteorológicos atuais diretamente da Open-Meteo
        sem salvar no banco de dados.

        Útil para APIs que precisam de dados em tempo real.

        Returns:
            Dicionário com dados atuais ou None em caso de erro
        """
        try:
            lat = float(self.cliente.latitude)
            lon = float(self.cliente.longitude)

            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m,wind_gusts_10m,wind_direction_10m,pressure_msl,weather_code',
                'timezone': 'America/Sao_Paulo',
            }

            response = requests.get(
                f"{self.BASE_URL_OPENMETEO}/forecast",
                params=params,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()

            dados = response.json()

            if not dados or 'current' not in dados:
                return None

            current = dados['current']

            # Mapear weather_code para descrição
            weather_codes = {
                0: 'Céu limpo',
                1: 'Principalmente limpo',
                2: 'Parcialmente nublado',
                3: 'Nublado',
                45: 'Neblina',
                48: 'Neblina com geada',
                51: 'Garoa leve',
                53: 'Garoa moderada',
                55: 'Garoa forte',
                61: 'Chuva leve',
                63: 'Chuva moderada',
                65: 'Chuva forte',
                80: 'Pancadas leves',
                81: 'Pancadas moderadas',
                82: 'Pancadas fortes',
                95: 'Tempestade',
                96: 'Tempestade com granizo leve',
                99: 'Tempestade com granizo forte',
            }

            weather_code = current.get('weather_code', 0)

            return {
                'latitude': dados.get('latitude'),
                'longitude': dados.get('longitude'),
                'altitude': dados.get('elevation'),
                'timezone': dados.get('timezone'),
                'data_hora': current.get('time'),
                'temperatura': current.get('temperature_2m'),
                'umidade': current.get('relative_humidity_2m'),
                'precipitacao': current.get('precipitation', 0) or current.get('rain', 0),
                'pressao': current.get('pressure_msl'),
                'vento_velocidade': current.get('wind_speed_10m'),
                'vento_rajada': current.get('wind_gusts_10m'),
                'vento_direcao': current.get('wind_direction_10m'),
                'weather_code': weather_code,
                'condicao': weather_codes.get(weather_code, 'Desconhecido'),
                'fonte': 'Open-Meteo',
            }

        except Exception as e:
            logger.error(f"Erro ao obter dados Open-Meteo: {e}")
            return None
