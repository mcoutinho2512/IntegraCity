"""
Integrador Waze Public Traffic Feeds
=====================================

Coleta dados de trânsito em tempo real do Waze:
- JAMs (congestionamentos)
- ALERTs (acidentes, perigos)
- IRREGULARities (interdições, obras)

Calcula nível de mobilidade (E1-E5) baseado em regras HEXAGON.

API: https://www.waze.com/row-partnerhub-api/feeds-tvt/

Nota: API pública para demonstração (não requer parceria CCP)
"""

import requests
from datetime import timedelta
from decimal import Decimal
from typing import Dict, Tuple, Optional, List
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class IntegradorWaze:
    """
    Integrador com Waze Public Traffic Feeds

    API Pública (não requer parceria CCP)
    Usado para demonstração e cidades sem parceria formal
    """

    BASE_URL = "https://www.waze.com/row-partnerhub-api"
    TIMEOUT = 20

    # Feed IDs conhecidos (demonstração)
    # Descobertos via inspeção de rede em https://www.waze.com/live-map
    FEED_IDS = {
        'rio-de-janeiro': '18577882871',
        'sao-paulo': '18577882872',
        'belo-horizonte': '18577882873',
        # Adicionar outros feeds conforme descobertos
    }

    # Limiares para níveis de mobilidade (baseado em HEXAGON)
    LIMIARES_JAMS = {
        5: 20,  # E5 (Crise): >= 20 jams severos
        4: 15,  # E4 (Alerta): >= 15 jams severos
        3: 10,  # E3 (Atenção): >= 10 jams severos
        2: 5,   # E2 (Mobilização): >= 5 jams severos
    }

    LIMIARES_ACIDENTES_MAIORES = {
        5: 4,   # E5: >= 4 acidentes graves
        4: 2,   # E4: >= 2 acidentes graves
        3: 1,   # E3: >= 1 acidente grave
    }

    LIMIARES_INTERDICOES = {
        5: 5,   # E5: >= 5 vias interditadas
        4: 3,   # E4: >= 3 vias interditadas
        3: 1,   # E3: >= 1 via interditada
    }

    def __init__(self, cliente):
        """
        Inicializa o integrador com um cliente específico

        Args:
            cliente: Instância do modelo Cliente
        """
        self.cliente = cliente

        # Obter feed_id da configuração do cliente
        self.feed_id = cliente.config_apis.get('waze_feed_id') if cliente.config_apis else None

        # Se não configurado, tentar inferir pela cidade
        if not self.feed_id:
            cidade_slug = cliente.cidade.lower().replace(' ', '-')
            self.feed_id = self.FEED_IDS.get(cidade_slug)

    def coletar_dados(self):
        """
        Coleta dados do feed Waze e armazena em DadosMobilidade

        Returns:
            DadosMobilidade object ou None
        """
        from ..models import DadosMobilidade

        if not self.feed_id:
            logger.warning(f"Cliente {self.cliente.nome} sem feed_id do Waze configurado")
            return None

        try:
            logger.info(f"Coletando dados Waze para {self.cliente.nome} (feed: {self.feed_id})")

            url = f"{self.BASE_URL}/feeds-tvt/"
            params = {'id': self.feed_id}

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': 'https://www.waze.com/live-map',
            }

            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            # Processar dados
            stats = self._processar_dados(data)

            # Salvar no banco (evitar duplicatas por hora)
            agora = timezone.now()
            # Arredondar para a hora mais próxima para evitar duplicatas
            data_hora_arredondada = agora.replace(minute=0, second=0, microsecond=0)

            # Verificar se já existe registro para esta hora
            existente = DadosMobilidade.objects.filter(
                cliente=self.cliente,
                data_hora__gte=data_hora_arredondada,
                data_hora__lt=data_hora_arredondada + timedelta(hours=1)
            ).first()

            if existente:
                # Atualizar registro existente com mapeamento explícito
                existente.total_jams = stats['total_jams']
                existente.jams_severos = stats['jams_severos']
                existente.jams_moderados = stats['jams_moderados']
                existente.jams_leves = stats['jams_leves']
                existente.total_alerts = stats['total_alerts']
                existente.acidentes_maiores = stats['acidentes_maiores']
                existente.acidentes_menores = stats['acidentes_menores']
                existente.perigos = stats['perigos']
                existente.total_irregularidades = stats['total_irregularidades']
                existente.vias_interditadas = stats['vias_interditadas']
                existente.obras = stats['obras']
                existente.velocidade_media_kmh = stats['velocidade_media']
                existente.atraso_medio_segundos = stats['atraso_medio']
                existente.extensao_total_congestionamentos_m = stats['extensao_total']
                existente.dados_raw = data
                existente.save()
                dados_obj = existente
                logger.info(f"Dados atualizados para {self.cliente.nome}")
            else:
                # Criar novo registro
                dados_obj = DadosMobilidade.objects.create(
                    cliente=self.cliente,
                    data_hora=agora,
                    total_jams=stats['total_jams'],
                    jams_severos=stats['jams_severos'],
                    jams_moderados=stats['jams_moderados'],
                    jams_leves=stats['jams_leves'],
                    total_alerts=stats['total_alerts'],
                    acidentes_maiores=stats['acidentes_maiores'],
                    acidentes_menores=stats['acidentes_menores'],
                    perigos=stats['perigos'],
                    total_irregularidades=stats['total_irregularidades'],
                    vias_interditadas=stats['vias_interditadas'],
                    obras=stats['obras'],
                    velocidade_media_kmh=stats['velocidade_media'],
                    atraso_medio_segundos=stats['atraso_medio'],
                    extensao_total_congestionamentos_m=stats['extensao_total'],
                    dados_raw=data,
                )
                logger.info(f"Novos dados criados para {self.cliente.nome}")

            logger.info(
                f"Dados coletados: {stats['total_jams']} jams ({stats['jams_severos']} severos), "
                f"{stats['total_alerts']} alerts ({stats['acidentes_maiores']} maiores), "
                f"{stats['total_irregularidades']} irregularidades ({stats['vias_interditadas']} interditadas)"
            )

            return dados_obj

        except requests.Timeout:
            logger.error(f"Timeout ao coletar dados Waze para {self.cliente.nome}")
            return None
        except requests.RequestException as e:
            logger.error(f"Erro HTTP ao coletar Waze: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao coletar dados Waze: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _processar_dados(self, data: Dict) -> Dict:
        """
        Processa dados brutos do Waze e extrai estatísticas

        Args:
            data: JSON retornado pela API Waze

        Returns:
            Dicionário com estatísticas processadas

        Nota: A API TVT (Traffic View Tool) usa estrutura diferente:
              - routes[].jamLevel = nível de congestionamento por rota
              - irregularities[type=DYNAMIC] = segmentos de congestionamento
              - NÃO há array 'jams' separado como na API CCP tradicional
        """
        routes = data.get('routes', [])
        alerts = data.get('alerts', [])
        irregularities = data.get('irregularities', [])

        # ========================================
        # API TVT: Usar routes.jamLevel e irregularities DYNAMIC
        # ========================================
        # Irregularities com type=DYNAMIC são os congestionamentos
        irregularidades_dinamicas = [
            i for i in irregularities
            if i.get('type') == 'DYNAMIC'
        ]

        # Calcular nível de severidade baseado no atraso (historicTime vs tempo atual)
        jams_severos = []
        jams_moderados = []
        jams_leves = []

        for irreg in irregularidades_dinamicas:
            historic_time = irreg.get('historicTime', 0)
            current_time = irreg.get('time', historic_time)
            # Calcular atraso percentual
            if historic_time > 0:
                atraso_pct = ((current_time - historic_time) / historic_time) * 100
                if atraso_pct >= 50:  # Atraso >= 50% = severo
                    jams_severos.append(irreg)
                elif atraso_pct >= 20:  # Atraso >= 20% = moderado
                    jams_moderados.append(irreg)
                else:
                    jams_leves.append(irreg)

        # Também usar jamLevel das routes para classificar
        for route in routes:
            jam_level = route.get('jamLevel', 0)
            if jam_level >= 4:  # Muito lento/parado
                jams_severos.append({'from_route': True, 'jamLevel': jam_level, 'name': route.get('name', '')})
            elif jam_level >= 2:  # Moderado
                jams_moderados.append({'from_route': True, 'jamLevel': jam_level, 'name': route.get('name', '')})

        # Total de "jams" = irregularidades dinâmicas (são os congestionamentos reais)
        total_jams = len(irregularidades_dinamicas)

        # Métricas de congestionamentos (usando irregularidades DYNAMIC)
        extensoes = [i.get('length', 0) for i in irregularidades_dinamicas]
        extensao_total = sum(extensoes)

        # Velocidade média estimada a partir do length/time
        velocidades = []
        for irreg in irregularidades_dinamicas:
            length_m = irreg.get('length', 0)
            time_s = irreg.get('time', 0)
            if time_s > 0 and length_m > 0:
                speed_kmh = (length_m / time_s) * 3.6  # m/s para km/h
                velocidades.append(speed_kmh)

        velocidade_media = sum(velocidades) / len(velocidades) if velocidades else None

        # Atraso médio (diferença entre tempo atual e histórico)
        atrasos = []
        for irreg in irregularidades_dinamicas:
            historic = irreg.get('historicTime', 0)
            current = irreg.get('time', 0)
            if historic > 0 and current > 0:
                atrasos.append(current - historic)

        atraso_medio = int(sum(atrasos) / len(atrasos)) if atrasos else None

        # ========================================
        # Processar ALERTs (Alertas) - se disponíveis
        # ========================================
        acidentes = [a for a in alerts if a.get('type') == 'ACCIDENT']
        perigos = [a for a in alerts if a.get('type') == 'HAZARD']

        acidentes_maiores = [
            a for a in acidentes
            if 'MAJOR' in a.get('subtype', '') or
               a.get('reportRating', 0) >= 4 or
               a.get('reliability', 0) >= 8
        ]

        acidentes_menores = [
            a for a in acidentes
            if a not in acidentes_maiores
        ]

        # ========================================
        # Processar IRREGULARities (Outras)
        # ========================================
        vias_interditadas = [
            i for i in irregularities
            if i.get('type') == 'ROAD_CLOSED'
        ]

        obras = [
            i for i in irregularities
            if i.get('type') == 'CONSTRUCTION'
        ]

        # Usar dados agregados do response
        # lengthOfJams é um array: [{'jamLevel': 1, 'jamLength': 30545}, ...]
        length_of_jams_data = data.get('lengthOfJams', [])
        if isinstance(length_of_jams_data, list):
            # Somar todos os comprimentos de jams
            length_of_jams = sum(item.get('jamLength', 0) for item in length_of_jams_data)
        else:
            length_of_jams = length_of_jams_data or 0

        # usersOnJams também é um array
        users_on_jams_data = data.get('usersOnJams', [])
        if isinstance(users_on_jams_data, list):
            users_on_jams = sum(item.get('wazersCount', 0) for item in users_on_jams_data)
        else:
            users_on_jams = users_on_jams_data or 0

        # Usar extensão das irregularidades DYNAMIC se não tiver lengthOfJams
        final_extensao = length_of_jams if length_of_jams > 0 else extensao_total

        # Log detalhado
        logger.info(
            f"Processado: {len(routes)} routes, {len(irregularidades_dinamicas)} congestionamentos, "
            f"{len(irregularities)} irregularities total, "
            f"extensão={final_extensao}m ({final_extensao/1000:.1f}km), users={users_on_jams}"
        )

        return {
            'total_jams': total_jams,  # Usando irregularidades DYNAMIC como jams
            'jams_severos': len(jams_severos),
            'jams_moderados': len(jams_moderados),
            'jams_leves': len(jams_leves),
            'total_alerts': len(alerts),
            'acidentes_maiores': len(acidentes_maiores),
            'acidentes_menores': len(acidentes_menores),
            'perigos': len(perigos),
            'total_irregularidades': len(irregularities),
            'vias_interditadas': len(vias_interditadas),
            'obras': len(obras),
            'velocidade_media': Decimal(str(round(velocidade_media, 2))) if velocidade_media else None,
            'atraso_medio': atraso_medio,
            'extensao_total': final_extensao,
        }

    def calcular_nivel_mobilidade(self) -> Tuple[int, Dict]:
        """
        Calcula nível de mobilidade (E1-E5) baseado em dados Waze

        Regras adaptadas da Matriz HEXAGON:
        - JAMs severos → equivalente a % de trânsito
        - Acidentes maiores → equivalente "modo vermelho"
        - Vias interditadas → critério direto

        Returns:
            Tupla (nivel, detalhes_dict)
        """
        from ..models import DadosMobilidade

        # Buscar dados mais recentes (última hora)
        limite = timezone.now() - timedelta(hours=1)
        dados_recentes = DadosMobilidade.objects.filter(
            cliente=self.cliente,
            data_hora__gte=limite
        ).order_by('-data_hora').first()

        if not dados_recentes:
            # Sem dados recentes - tentar coletar agora
            logger.warning(f"Sem dados de mobilidade recentes para {self.cliente.nome}")
            return 1, {
                'nivel': 1,
                'nomenclatura': 'Normal',
                'erro': 'Sem dados de mobilidade recentes',
                'razao': 'Última coleta há mais de 1 hora. Execute: coletar_mobilidade',
                'cor': '#00ff88',
            }

        # Aplicar regras HEXAGON adaptadas
        nivel = 1  # Normal por padrão
        razoes = []

        jams_severos = dados_recentes.jams_severos
        acidentes_maiores = dados_recentes.acidentes_maiores
        acidentes_menores = dados_recentes.acidentes_menores
        vias_interditadas = dados_recentes.vias_interditadas
        perigos = dados_recentes.perigos

        # ========================================
        # REGRA 1: JAMs severos (congestionamentos graves)
        # Baseado na quantidade de pontos com trânsito muito lento
        # ========================================
        if jams_severos >= self.LIMIARES_JAMS[5]:
            nivel = max(nivel, 5)
            razoes.append(f'{jams_severos} congestionamentos SEVEROS (Crise)')
        elif jams_severos >= self.LIMIARES_JAMS[4]:
            nivel = max(nivel, 4)
            razoes.append(f'{jams_severos} congestionamentos SEVEROS (Alerta)')
        elif jams_severos >= self.LIMIARES_JAMS[3]:
            nivel = max(nivel, 3)
            razoes.append(f'{jams_severos} congestionamentos SEVEROS (Atenção)')
        elif jams_severos >= self.LIMIARES_JAMS[2]:
            nivel = max(nivel, 2)
            razoes.append(f'{jams_severos} congestionamentos severos (Mobilização)')

        # ========================================
        # REGRA 2: Acidentes (equivalente CIMU)
        # Acidentes maiores = modo vermelho
        # Acidentes menores = modo amarelo
        # ========================================
        if acidentes_maiores >= self.LIMIARES_ACIDENTES_MAIORES[5]:
            nivel = max(nivel, 5)
            razoes.append(f'{acidentes_maiores} ACIDENTES GRAVES (Crise)')
        elif acidentes_maiores >= self.LIMIARES_ACIDENTES_MAIORES[4]:
            nivel = max(nivel, 4)
            razoes.append(f'{acidentes_maiores} ACIDENTES GRAVES (Alerta)')
        elif acidentes_maiores >= self.LIMIARES_ACIDENTES_MAIORES[3]:
            nivel = max(nivel, 3)
            razoes.append(f'{acidentes_maiores} acidente(s) grave(s) (Atenção)')
        elif acidentes_menores >= 5:
            nivel = max(nivel, 3)
            razoes.append(f'{acidentes_menores} acidentes leves (Atenção)')
        elif acidentes_menores >= 2:
            nivel = max(nivel, 2)
            razoes.append(f'{acidentes_menores} acidentes leves (Mobilização)')

        # ========================================
        # REGRA 3: Interdições (critério direto HEXAGON)
        # ========================================
        if vias_interditadas >= self.LIMIARES_INTERDICOES[5]:
            nivel = max(nivel, 5)
            razoes.append(f'{vias_interditadas} VIAS INTERDITADAS (Crise)')
        elif vias_interditadas >= self.LIMIARES_INTERDICOES[4]:
            nivel = max(nivel, 4)
            razoes.append(f'{vias_interditadas} vias interditadas (Alerta)')
        elif vias_interditadas >= self.LIMIARES_INTERDICOES[3]:
            nivel = max(nivel, 3)
            razoes.append(f'{vias_interditadas} via(s) interditada(s) (Atenção)')

        # ========================================
        # REGRA 4: Perigos na via (bônus)
        # ========================================
        if perigos >= 10:
            nivel = max(nivel, min(nivel + 1, 5))
            razoes.append(f'{perigos} perigos reportados na via')

        # Cores por nível (padrão COR Rio E1-E5)
        CORES_NIVEL = {
            1: '#00ff88',   # Verde - Normal
            2: '#00D4FF',   # Cyan - Mobilização
            3: '#FFB800',   # Amarelo - Atenção
            4: '#FF6B00',   # Laranja - Alerta
            5: '#FF0055',   # Vermelho - Crise
        }

        NOMENCLATURA = {
            1: 'Normal',
            2: 'Mobilização',
            3: 'Atenção',
            4: 'Alerta',
            5: 'Crise',
        }

        # Montar detalhes
        detalhes = {
            'nivel': nivel,
            'nomenclatura': NOMENCLATURA.get(nivel, 'Normal'),
            'cor': CORES_NIVEL.get(nivel, '#00ff88'),
            'data_hora': dados_recentes.data_hora.isoformat(),
            'idade_minutos': dados_recentes.idade_minutos,
            'total_jams': dados_recentes.total_jams,
            'jams_severos': jams_severos,
            'jams_moderados': dados_recentes.jams_moderados,
            'jams_leves': dados_recentes.jams_leves,
            'total_alerts': dados_recentes.total_alerts,
            'acidentes_maiores': acidentes_maiores,
            'acidentes_menores': acidentes_menores,
            'perigos': perigos,
            'total_irregularidades': dados_recentes.total_irregularidades,
            'vias_interditadas': vias_interditadas,
            'obras': dados_recentes.obras,
            'velocidade_media_kmh': float(dados_recentes.velocidade_media_kmh) if dados_recentes.velocidade_media_kmh else None,
            'atraso_medio_minutos': round(dados_recentes.atraso_medio_segundos / 60, 1) if dados_recentes.atraso_medio_segundos else None,
            'extensao_total_km': dados_recentes.extensao_total_km,
            'razao': '; '.join(razoes) if razoes else 'Mobilidade normal - trânsito fluindo',
            'fonte': 'Waze',
        }

        logger.info(f"Grupo 3 (Mobilidade) para {self.cliente.nome}: Nível E{nivel} - {detalhes['razao']}")

        return nivel, detalhes

    def obter_resumo_mobilidade(self) -> Dict:
        """
        Retorna resumo dos dados de mobilidade para dashboard

        Returns:
            Dicionário com resumo atual
        """
        from ..models import DadosMobilidade

        limite = timezone.now() - timedelta(hours=24)
        dados = DadosMobilidade.objects.filter(
            cliente=self.cliente,
            data_hora__gte=limite
        ).order_by('-data_hora')

        if not dados.exists():
            return {
                'disponivel': False,
                'erro': 'Sem dados de mobilidade nas últimas 24h'
            }

        ultimo = dados.first()
        nivel, detalhes = self.calcular_nivel_mobilidade()

        # Estatísticas das últimas 24h
        total_registros = dados.count()
        media_jams = sum(d.total_jams for d in dados) / total_registros if total_registros else 0
        max_jams = max(d.total_jams for d in dados) if dados else 0
        total_acidentes_24h = sum(d.acidentes_maiores + d.acidentes_menores for d in dados)

        return {
            'disponivel': True,
            'nivel_atual': nivel,
            'detalhes': detalhes,
            'ultimo_dado': {
                'data_hora': ultimo.data_hora.isoformat(),
                'idade_minutos': ultimo.idade_minutos,
                'total_jams': ultimo.total_jams,
                'jams_severos': ultimo.jams_severos,
            },
            'estatisticas_24h': {
                'total_registros': total_registros,
                'media_jams': round(media_jams, 1),
                'max_jams': max_jams,
                'total_acidentes': total_acidentes_24h,
            }
        }

    def obter_jams_para_mapa(self) -> List[Dict]:
        """
        Retorna lista de congestionamentos para plotar no mapa

        Returns:
            Lista de dicts com coordenadas e info dos jams
        """
        from ..models import DadosMobilidade

        # Buscar dados mais recentes
        limite = timezone.now() - timedelta(hours=1)
        dados = DadosMobilidade.objects.filter(
            cliente=self.cliente,
            data_hora__gte=limite
        ).order_by('-data_hora').first()

        if not dados or not dados.dados_raw:
            return []

        # Extrair jams de dentro das routes (API TVT)
        routes = dados.dados_raw.get('routes', [])
        jams_raw = []
        for route in routes:
            route_jams = route.get('jams', [])
            jams_raw.extend(route_jams)

        # Fallback para API com jams no nível raiz
        if not jams_raw:
            jams_raw = dados.dados_raw.get('jams', [])

        jams_formatados = []

        for jam in jams_raw[:100]:  # Limitar a 100 para performance
            # Extrair coordenadas da linha do congestionamento
            line = jam.get('line', [])
            if not line:
                continue

            jams_formatados.append({
                'id': jam.get('uuid', jam.get('id')),
                'street': jam.get('street', 'Via não identificada'),
                'city': jam.get('city', ''),
                'level': jam.get('level', 0),
                'speed': jam.get('speedKMH', 0),
                'length': jam.get('length', 0),
                'delay': jam.get('delay', 0),
                'type': jam.get('type', ''),
                'coordinates': [(p.get('x'), p.get('y')) for p in line],
            })

        # Também incluir irregularidades DYNAMIC como jams (são congestionamentos)
        irregularities = dados.dados_raw.get('irregularities', [])
        for irreg in irregularities:
            if irreg.get('type') == 'DYNAMIC':
                line = irreg.get('line', [])
                if not line:
                    continue

                # Extrair nome da via (name contém "Av. Brasil,Rio de Janeiro")
                street_name = irreg.get('name', '') or irreg.get('toName', '') or 'Via monitorada'
                # Remover sufixo de cidade se presente
                if ',' in street_name:
                    parts = street_name.split(',')
                    if len(parts) >= 2 and parts[-1].strip().lower() in [
                        'rio de janeiro', 'niteroi', 'niterói', 'sao goncalo',
                        'são gonçalo', 'duque de caxias', 'nova iguacu', 'nova iguaçu'
                    ]:
                        street_name = ','.join(parts[:-1]).strip()

                # Calcular velocidade a partir de length/time
                length_m = irreg.get('length', 0)
                time_s = irreg.get('time', 0)
                speed = (length_m / time_s * 3.6) if time_s > 0 else 0

                # Calcular atraso
                historic_time = irreg.get('historicTime', 0)
                delay = time_s - historic_time if historic_time > 0 else 0

                jams_formatados.append({
                    'id': irreg.get('id', ''),
                    'street': street_name,
                    'city': irreg.get('city', ''),
                    'level': irreg.get('jamLevel', 3),  # Usar jamLevel real
                    'speed': round(speed, 1),
                    'length': length_m,
                    'delay': delay,
                    'type': 'DYNAMIC',
                    'coordinates': [(p.get('x'), p.get('y')) for p in line],
                })

        return jams_formatados

    def obter_alerts_para_mapa(self) -> List[Dict]:
        """
        Retorna lista de alertas para plotar no mapa

        Returns:
            Lista de dicts com coordenadas e info dos alerts
        """
        from ..models import DadosMobilidade

        limite = timezone.now() - timedelta(hours=1)
        dados = DadosMobilidade.objects.filter(
            cliente=self.cliente,
            data_hora__gte=limite
        ).order_by('-data_hora').first()

        if not dados or not dados.dados_raw:
            return []

        alerts_raw = dados.dados_raw.get('alerts', [])
        alerts_formatados = []

        for alert in alerts_raw[:50]:  # Limitar a 50
            location = alert.get('location', {})
            if not location:
                continue

            alerts_formatados.append({
                'id': alert.get('uuid', ''),
                'type': alert.get('type', ''),
                'subtype': alert.get('subtype', ''),
                'street': alert.get('street', 'Local não identificado'),
                'city': alert.get('city', ''),
                'confidence': alert.get('confidence', 0),
                'reliability': alert.get('reliability', 0),
                'lat': location.get('y'),
                'lon': location.get('x'),
            })

        return alerts_formatados

    def obter_dados_completos_mapa(self) -> Dict:
        """
        Retorna todos os dados do Waze categorizados para o mapa

        Returns:
            Dict com:
                - congestionamentos: Lista de jams (DYNAMIC)
                - interdicoes: Lista de vias interditadas (ROAD_CLOSED)
                - eventos: Lista de eventos especiais (STATIC com nome)
                - rotas_transito: Rotas com trânsito alto (jamLevel >= 3)
                - alertas: Acidentes, perigos, etc
                - estatisticas: Contagens por tipo
        """
        from ..models import DadosMobilidade

        limite = timezone.now() - timedelta(hours=1)
        dados = DadosMobilidade.objects.filter(
            cliente=self.cliente,
            data_hora__gte=limite
        ).order_by('-data_hora').first()

        resultado = {
            'congestionamentos': [],
            'interdicoes': [],
            'eventos': [],
            'rotas_transito': [],
            'alertas': [],
            'estatisticas': {
                'total_congestionamentos': 0,
                'total_interdicoes': 0,
                'total_eventos': 0,
                'total_rotas_transito': 0,
                'total_alertas': 0,
            }
        }

        if not dados or not dados.dados_raw:
            return resultado

        raw = dados.dados_raw
        irregularities = raw.get('irregularities', [])
        routes = raw.get('routes', [])
        alerts = raw.get('alerts', [])

        # Helper para limpar nome de cidade
        def limpar_nome(nome):
            if not nome:
                return 'Via não identificada'
            if ',' in nome:
                parts = nome.split(',')
                if len(parts) >= 2 and parts[-1].strip().lower() in [
                    'rio de janeiro', 'niteroi', 'niterói', 'sao goncalo',
                    'são gonçalo', 'duque de caxias', 'nova iguacu', 'nova iguaçu'
                ]:
                    return ','.join(parts[:-1]).strip()
            return nome

        # ========================================
        # 1. CONGESTIONAMENTOS (DYNAMIC)
        # ========================================
        for irreg in irregularities:
            if irreg.get('type') != 'DYNAMIC':
                continue

            line = irreg.get('line', [])
            if not line:
                continue

            length_m = irreg.get('length', 0)
            time_s = irreg.get('time', 0)
            speed = (length_m / time_s * 3.6) if time_s > 0 else 0
            historic_time = irreg.get('historicTime', 0)
            delay = time_s - historic_time if historic_time > 0 else 0

            resultado['congestionamentos'].append({
                'id': str(irreg.get('id', '')),
                'category': 'congestionamento',
                'street': limpar_nome(irreg.get('name', '')),
                'toName': irreg.get('toName', ''),
                'level': irreg.get('jamLevel', 3),
                'speed': round(speed, 1),
                'length': length_m,
                'delay': delay,
                'coordinates': [(p.get('x'), p.get('y')) for p in line],
            })

        # ========================================
        # 2. INTERDIÇÕES E EVENTOS (STATIC)
        # ========================================
        for irreg in irregularities:
            if irreg.get('type') != 'STATIC':
                continue

            # Verificar subRoutes para ROAD_CLOSED
            sub_routes = irreg.get('subRoutes', [])
            is_road_closed = False
            alert_info = None

            for sr in sub_routes:
                lead_alert = sr.get('leadAlert', {})
                if lead_alert.get('type') == 'ROAD_CLOSED':
                    is_road_closed = True
                    alert_info = lead_alert
                    break

            nome = limpar_nome(irreg.get('name', ''))
            line = irreg.get('line', [])

            # Se não tem line principal, usar das subRoutes
            if not line and sub_routes:
                all_coords = []
                for sr in sub_routes:
                    sr_line = sr.get('line', [])
                    all_coords.extend([(p.get('x'), p.get('y')) for p in sr_line])
                coords = all_coords
            else:
                coords = [(p.get('x'), p.get('y')) for p in line] if line else []

            if not coords:
                continue

            item = {
                'id': str(irreg.get('id', '')),
                'street': nome,
                'length': irreg.get('length', 0),
                'coordinates': coords,
            }

            if is_road_closed:
                item['category'] = 'interdicao'
                item['reason'] = nome
                item['alert_street'] = alert_info.get('street', '') if alert_info else ''
                resultado['interdicoes'].append(item)
            else:
                item['category'] = 'evento'
                resultado['eventos'].append(item)

        # ========================================
        # 3. ROTAS COM TRÂNSITO ALTO (jamLevel >= 3)
        # ========================================
        for route in routes:
            jam_level = route.get('jamLevel', 0)
            if jam_level < 3:  # Só mostrar trânsito moderado+
                continue

            line = route.get('line', [])
            if not line:
                continue

            length_m = route.get('length', 0)
            time_s = route.get('time', 0)
            speed = (length_m / time_s * 3.6) if time_s > 0 else 0

            resultado['rotas_transito'].append({
                'id': str(route.get('id', '')),
                'category': 'rota_transito',
                'name': limpar_nome(route.get('name', '')),
                'fromName': route.get('fromName', ''),
                'toName': route.get('toName', ''),
                'level': jam_level,
                'speed': round(speed, 1),
                'length': length_m,
                'coordinates': [(p.get('x'), p.get('y')) for p in line],
            })

        # ========================================
        # 4. ALERTAS (Acidentes, Perigos, etc)
        # ========================================
        for alert in alerts[:100]:
            location = alert.get('location', {})
            if not location:
                continue

            alert_type = alert.get('type', '')
            subtype = alert.get('subtype', '')

            # Mapear ícones por tipo
            icon_map = {
                'ACCIDENT': 'fa-car-crash',
                'HAZARD': 'fa-exclamation-triangle',
                'ROAD_CLOSED': 'fa-road-barrier',
                'JAM': 'fa-car',
                'POLICE': 'fa-user-shield',
                'CONSTRUCTION': 'fa-hard-hat',
            }

            resultado['alertas'].append({
                'id': alert.get('uuid', alert.get('id', '')),
                'category': 'alerta',
                'type': alert_type,
                'subtype': subtype,
                'street': alert.get('street', 'Local não identificado'),
                'city': alert.get('city', ''),
                'confidence': alert.get('confidence', 0),
                'reliability': alert.get('reliability', 0),
                'lat': location.get('y'),
                'lon': location.get('x'),
                'icon': icon_map.get(alert_type, 'fa-info-circle'),
            })

        # Estatísticas
        resultado['estatisticas'] = {
            'total_congestionamentos': len(resultado['congestionamentos']),
            'total_interdicoes': len(resultado['interdicoes']),
            'total_eventos': len(resultado['eventos']),
            'total_rotas_transito': len(resultado['rotas_transito']),
            'total_alertas': len(resultado['alertas']),
        }

        return resultado

    def processar_congestionamentos_detalhados(self, dados_mobilidade=None):
        """
        Processa dados brutos e cria registros de CongestionamentoVia
        vinculados aos logradouros oficiais

        Args:
            dados_mobilidade: Objeto DadosMobilidade (usa mais recente se None)

        Returns:
            dict: Estatisticas do processamento
        """
        from ..models import DadosMobilidade, CongestionamentoVia, Logradouro
        from .via_matcher import get_via_matcher

        # Buscar dados mais recentes se nao fornecido
        if not dados_mobilidade:
            limite = timezone.now() - timedelta(hours=1)
            dados_mobilidade = DadosMobilidade.objects.filter(
                cliente=self.cliente,
                data_hora__gte=limite
            ).order_by('-data_hora').first()

        if not dados_mobilidade or not dados_mobilidade.dados_raw:
            logger.warning(f"Sem dados para processar congestionamentos - {self.cliente.nome}")
            return {'erro': 'Sem dados disponíveis'}

        # Verificar se ja existem logradouros importados
        if not Logradouro.objects.exists():
            logger.warning("Nenhum logradouro importado. Execute: python manage.py importar_logradouros")
            return {'erro': 'Logradouros nao importados'}

        # Inicializar matcher
        matcher = get_via_matcher()

        # Estatisticas
        stats = {
            'total_processados': 0,
            'match_exato': 0,
            'match_fuzzy': 0,
            'nao_encontrados': 0,
            'criticidade': {
                'normal': 0,
                'leve': 0,
                'moderada': 0,
                'severa': 0,
                'critica': 0,
            }
        }

        agora = timezone.now()
        raw_data = dados_mobilidade.dados_raw

        # Processar routes (API TVT)
        routes = raw_data.get('routes', [])
        for route in routes:
            via_nome = route.get('name', '') or route.get('fromName', '')
            if not via_nome:
                continue

            jam_level = route.get('jamLevel', 0)
            if jam_level < 2:  # Ignorar transito livre/leve
                continue

            # Calcular velocidade estimada
            length = route.get('length', 0)
            time_s = route.get('time', 0)
            velocidade = (length / time_s * 3.6) if time_s > 0 else None

            # Buscar logradouro oficial
            logradouro, score, metodo = matcher.buscar_via(via_nome)

            # Extrair coordenadas do primeiro ponto
            line = route.get('line', [])
            lat = line[0].get('y') if line else None
            lon = line[0].get('x') if line else None

            # Calcular atraso
            historic_time = route.get('historicTime', 0)
            current_time = route.get('time', 0)
            atraso = current_time - historic_time if historic_time > 0 else None

            # Criar registro
            congestionamento = CongestionamentoVia(
                cliente=self.cliente,
                dados_mobilidade=dados_mobilidade,
                logradouro=logradouro,
                data_hora=agora,
                via_nome_waze=via_nome,
                jam_level=jam_level,
                velocidade_atual=Decimal(str(round(velocidade, 2))) if velocidade else None,
                atraso_segundos=atraso,
                extensao_metros=length,
                latitude=Decimal(str(lat)) if lat else None,
                longitude=Decimal(str(lon)) if lon else None,
                match_score=score,
                match_metodo=metodo,
            )
            congestionamento.save()  # Trigger calculo de criticidade

            # Atualizar estatisticas
            stats['total_processados'] += 1
            if metodo and 'exato' in metodo:
                stats['match_exato'] += 1
            elif metodo and 'fuzzy' in metodo:
                stats['match_fuzzy'] += 1
            else:
                stats['nao_encontrados'] += 1
            stats['criticidade'][congestionamento.criticidade] += 1

        # Processar irregularities DYNAMIC (congestionamentos)
        irregularities = raw_data.get('irregularities', [])
        for irreg in irregularities:
            if irreg.get('type') != 'DYNAMIC':
                continue

            via_nome = irreg.get('street', '') or irreg.get('name', '')
            if not via_nome:
                via_nome = 'Via monitorada'

            # Calcular velocidade a partir de length/time
            length = irreg.get('length', 0)
            time_s = irreg.get('time', 0)
            velocidade = (length / time_s * 3.6) if time_s > 0 else None

            # Calcular jam_level baseado no atraso
            historic_time = irreg.get('historicTime', 0)
            atraso_pct = ((time_s - historic_time) / historic_time * 100) if historic_time > 0 else 0

            if atraso_pct >= 100:
                jam_level = 5
            elif atraso_pct >= 50:
                jam_level = 4
            elif atraso_pct >= 20:
                jam_level = 3
            else:
                jam_level = 2

            # Buscar logradouro
            logradouro, score, metodo = matcher.buscar_via(via_nome)

            # Coordenadas
            line = irreg.get('line', [])
            lat = line[0].get('y') if line else None
            lon = line[0].get('x') if line else None

            atraso = time_s - historic_time if historic_time > 0 else None

            congestionamento = CongestionamentoVia(
                cliente=self.cliente,
                dados_mobilidade=dados_mobilidade,
                logradouro=logradouro,
                data_hora=agora,
                via_nome_waze=via_nome,
                jam_level=jam_level,
                velocidade_atual=Decimal(str(round(velocidade, 2))) if velocidade else None,
                atraso_segundos=atraso,
                extensao_metros=length,
                latitude=Decimal(str(lat)) if lat else None,
                longitude=Decimal(str(lon)) if lon else None,
                match_score=score,
                match_metodo=metodo,
            )
            congestionamento.save()

            stats['total_processados'] += 1
            if metodo and 'exato' in metodo:
                stats['match_exato'] += 1
            elif metodo and 'fuzzy' in metodo:
                stats['match_fuzzy'] += 1
            else:
                stats['nao_encontrados'] += 1
            stats['criticidade'][congestionamento.criticidade] += 1

        logger.info(
            f"Processados {stats['total_processados']} congestionamentos para {self.cliente.nome}: "
            f"{stats['match_exato']} exatos, {stats['match_fuzzy']} fuzzy, "
            f"{stats['nao_encontrados']} nao encontrados"
        )

        return stats

    def obter_congestionamentos_criticos(self, limit: int = 10) -> List[Dict]:
        """
        Retorna lista dos congestionamentos mais criticos (com dados oficiais)

        Args:
            limit: Numero maximo de registros

        Returns:
            Lista de dicts com dados combinados Waze + Logradouro
        """
        from ..models import CongestionamentoVia

        limite = timezone.now() - timedelta(hours=1)

        congestionamentos = CongestionamentoVia.objects.filter(
            cliente=self.cliente,
            data_hora__gte=limite,
            criticidade__in=['moderada', 'severa', 'critica']
        ).select_related('logradouro').order_by(
            '-criticidade', '-jam_level', '-extensao_metros'
        )[:limit]

        resultado = []
        for cong in congestionamentos:
            item = {
                'via_waze': cong.via_nome_waze,
                'jam_level': cong.jam_level,
                'velocidade_atual': float(cong.velocidade_atual) if cong.velocidade_atual else None,
                'atraso_segundos': cong.atraso_segundos,
                'extensao_metros': cong.extensao_metros,
                'criticidade': cong.criticidade,
                'percentual_deficit': cong.percentual_abaixo_regulamentada,
                'latitude': float(cong.latitude) if cong.latitude else None,
                'longitude': float(cong.longitude) if cong.longitude else None,
                'match_score': cong.match_score,
                'match_metodo': cong.match_metodo,
            }

            # Dados oficiais do logradouro
            if cong.logradouro:
                item['oficial'] = {
                    'nome_completo': cong.logradouro.nome_completo,
                    'bairro': cong.logradouro.bairro,
                    'hierarquia': cong.logradouro.hierarquia,
                    'velocidade_regulamentada': cong.logradouro.velocidade_regulamentada,
                    'tipo_trecho': cong.logradouro.tipo_trecho,
                }
            else:
                item['oficial'] = None

            resultado.append(item)

        return resultado
    def obter_vias_engarrafadas(self, nivel_minimo=2):
        """
        Retorna lista de vias com congestionamento
        
        Args:
            nivel_minimo: Nivel minimo de jam (0-4)
        
        Returns:
            Lista de dicts com dados das vias
        """
        from ..models import DadosMobilidade
        
        # Buscar ultimo dado coletado
        ultimo = DadosMobilidade.objects.filter(
            cliente=self.cliente
        ).order_by('-data_hora').first()
        
        if not ultimo or not ultimo.dados_raw:
            return []
        
        vias = []
        data_raw = ultimo.dados_raw
        
        # Processar rotas principais
        routes = data_raw.get('routes', [])
        for route in routes:
            jam_level = route.get('jamLevel', 0)
            
            if jam_level >= nivel_minimo:
                # Calcular atraso %
                historic_time = route.get('historicTime', 0)
                current_time = route.get('time', 0)
                
                atraso_percent = 0
                if historic_time > 0:
                    atraso_percent = ((current_time - historic_time) / historic_time) * 100
                
                vias.append({
                    'nome': route.get('name', 'Via não identificada'),
                    'origem': route.get('fromName', ''),
                    'destino': route.get('toName', ''),
                    'nivel': jam_level,
                    'nivel_texto': self._get_jam_level_text(jam_level),
                    'cor': self._get_jam_level_color(jam_level),
                    'extensao_m': route.get('length', 0),
                    'extensao_km': round(route.get('length', 0) / 1000, 1),
                    'tempo_historico_min': round(historic_time / 60, 1) if historic_time else 0,
                    'tempo_atual_min': round(current_time / 60, 1) if current_time else 0,
                    'atraso_percent': round(atraso_percent, 1),
                })
        
        # Processar sub-rotas (trechos específicos)
        for route in routes:
            sub_routes = route.get('subRoutes', [])
            for sub in sub_routes:
                jam_level = sub.get('jamLevel', 0)
                
                if jam_level >= nivel_minimo:
                    historic_time = sub.get('historicTime', 0)
                    current_time = sub.get('time', 0)
                    
                    atraso_percent = 0
                    if historic_time > 0:
                        atraso_percent = ((current_time - historic_time) / historic_time) * 100
                    
                    vias.append({
                        'nome': f"{sub.get('fromName', '')} → {sub.get('toName', '')}",
                        'origem': sub.get('fromName', ''),
                        'destino': sub.get('toName', ''),
                        'nivel': jam_level,
                        'nivel_texto': self._get_jam_level_text(jam_level),
                        'cor': self._get_jam_level_color(jam_level),
                        'extensao_m': sub.get('length', 0),
                        'extensao_km': round(sub.get('length', 0) / 1000, 1),
                        'tempo_historico_min': round(historic_time / 60, 1) if historic_time else 0,
                        'tempo_atual_min': round(current_time / 60, 1) if current_time else 0,
                        'atraso_percent': round(atraso_percent, 1),
                    })
        
        # Ordenar por nível (maior primeiro) e depois por atraso
        vias.sort(key=lambda x: (-x['nivel'], -x['atraso_percent']))
        
        return vias
    
    def obter_alertas_categorizados(self):
        """
        Retorna alertas separados por categoria
        
        Returns:
            Dict com categorias de alertas
        """
        from ..models import DadosMobilidade
        
        ultimo = DadosMobilidade.objects.filter(
            cliente=self.cliente
        ).order_by('-data_hora').first()
        
        if not ultimo or not ultimo.dados_raw:
            return {
                'acidentes': [],
                'interdicoes': [],
                'perigos': [],
                'outros': [],
            }
        
        data_raw = ultimo.dados_raw
        alerts = data_raw.get('alerts', [])
        irregularities = data_raw.get('irregularities', [])
        
        acidentes = []
        interdicoes = []
        perigos = []
        outros = []
        
        # Processar alerts
        for alert in alerts:
            alert_type = alert.get('type', '')
            subtype = alert.get('subtype', '')
            location = alert.get('location', {})
            
            item = {
                'tipo': alert_type,
                'subtipo': subtype,
                'rua': alert.get('street', 'Local não identificado'),
                'cidade': alert.get('city', ''),
                'confianca': alert.get('confidence', 0),
                'confiabilidade': alert.get('reliability', 0),
                'latitude': location.get('y'),
                'longitude': location.get('x'),
                'timestamp': alert.get('pubMillis', 0),
            }
            
            if 'ACCIDENT' in alert_type:
                item['gravidade'] = 'GRAVE' if 'MAJOR' in subtype else 'LEVE'
                acidentes.append(item)
            elif 'HAZARD' in alert_type or 'WEATHERHAZARD' in alert_type:
                perigos.append(item)
            elif 'ROAD_CLOSED' in alert_type:
                interdicoes.append(item)
            else:
                outros.append(item)
        
        # Processar irregularities
        for irreg in irregularities:
            irreg_type = irreg.get('type', '')
            
            item = {
                'tipo': irreg_type,
                'subtipo': '',
                'rua': irreg.get('street', 'Via não identificada'),
                'cidade': '',
                'confianca': 10,  # Irregularities são oficiais
                'confiabilidade': 10,
                'severidade': irreg.get('severity', 0),
                'inicio': irreg.get('startTimeMillis', 0),
                'fim': irreg.get('endTimeMillis', 0),
            }
            
            if 'ROAD_CLOSED' in irreg_type:
                interdicoes.append(item)
            elif 'CONSTRUCTION' in irreg_type:
                item['categoria'] = 'OBRAS'
                outros.append(item)
            else:
                outros.append(item)
        
        return {
            'acidentes': acidentes,
            'interdicoes': interdicoes,
            'perigos': perigos,
            'outros': outros,
            'total': len(acidentes) + len(interdicoes) + len(perigos) + len(outros),
        }
    
    def _get_jam_level_text(self, level):
        """Retorna texto descritivo do nível de congestionamento"""
        levels = {
            0: 'Livre',
            1: 'Lento',
            2: 'Moderado',
            3: 'Intenso',
            4: 'Parado',
        }
        return levels.get(level, 'Desconhecido')
    
    def _get_jam_level_color(self, level):
        """Retorna cor do nível de congestionamento"""
        colors = {
            0: '#00ff88',  # Verde
            1: '#FFB800',  # Amarelo
            2: '#FF6B00',  # Laranja
            3: '#FF0055',  # Vermelho
            4: '#8B0000',  # Vermelho escuro
        }
        return colors.get(level, '#6c757d')