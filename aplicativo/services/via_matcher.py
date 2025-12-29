"""
Servico de Matching de Vias
============================

Faz matching entre nomes de vias retornados pelo Waze e logradouros oficiais
do Rio de Janeiro.

Estrategias de matching:
1. Match exato (case insensitive)
2. Match normalizado (sem acentos)
3. Fuzzy match (fuzzywuzzy ratio)
4. Fuzzy parcial (partial_ratio para nomes incompletos)

Exemplo:
    matcher = ViaMatcher()
    logradouro, score, metodo = matcher.buscar_via("Av. Visconde de Albuquerque")
    # logradouro = <Logradouro: Av. Visconde de Albuquerque>
    # score = 100
    # metodo = 'exato'
"""

import unicodedata
import logging
from typing import Optional, Tuple
from django.db.models import Q
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)


class ViaMatcher:
    """
    Faz matching entre nomes de vias do Waze e logradouros oficiais

    Usa cache em memoria para vias importantes (arteriais/coletoras)
    para performance otima durante coleta em tempo real.
    """

    # Thresholds de confianca
    SCORE_EXATO = 100
    SCORE_MINIMO_FUZZY = 85        # Fuzzy ratio minimo para aceitar
    SCORE_MINIMO_PARCIAL = 75      # Partial ratio minimo
    SCORE_MINIMO_TOKEN = 80        # Token set ratio minimo

    # Abreviacoes comuns para normalizacao
    ABREVIACOES = {
        'av': 'avenida',
        'av.': 'avenida',
        'r': 'rua',
        'r.': 'rua',
        'pç': 'praca',
        'pça': 'praca',
        'pc': 'praca',
        'etr': 'estrada',
        'estr': 'estrada',
        'est': 'estrada',
        'trv': 'travessa',
        'tv': 'travessa',
        'al': 'alameda',
        'ld': 'ladeira',
        'lad': 'ladeira',
        'bc': 'beco',
        'vl': 'vila',
        'lrg': 'largo',
        'lg': 'largo',
        'cam': 'caminho',
        'via': 'via',
        'vd': 'viaduto',
        'tn': 'tunel',
        'aut': 'autoestrada',
        'rod': 'rodovia',
        'br': 'rodovia',
    }

    def __init__(self, carregar_cache: bool = True):
        """
        Inicializa o matcher

        Args:
            carregar_cache: Se True, carrega vias importantes em memoria
        """
        self._cache_vias = {}
        self._cache_nomes_normalizados = {}

        if carregar_cache:
            self._carregar_cache()

    def _carregar_cache(self):
        """Carrega vias importantes em memoria para matching rapido"""
        from ..models import Logradouro

        logger.info("Carregando cache de logradouros...")

        # Priorizar vias arteriais e coletoras (mais importantes para transito)
        vias_importantes = Logradouro.objects.filter(
            Q(hierarquia__in=['Arterial primária', 'Arterial secundária', 'Coletora']) |
            Q(velocidade_regulamentada__isnull=False)
        ).only(
            'cod_trecho', 'nome_completo', 'nome_parcial', 'tipo_extenso',
            'bairro', 'hierarquia', 'velocidade_regulamentada'
        )

        for via in vias_importantes:
            if via.nome_completo:
                chave = self._normalizar(via.nome_completo)
                self._cache_vias[chave] = via
                self._cache_nomes_normalizados[via.cod_trecho] = chave

        logger.info(f"Cache carregado: {len(self._cache_vias):,} vias importantes")

    def _normalizar(self, texto: str) -> str:
        """
        Normaliza texto para comparacao

        - Remove acentos
        - Converte para minusculas
        - Remove espacos extras
        - Expande abreviacoes comuns

        Args:
            texto: Texto original

        Returns:
            Texto normalizado
        """
        if not texto:
            return ""

        # Minusculas
        texto = texto.lower().strip()

        # Remove acentos
        texto = unicodedata.normalize('NFKD', texto)
        texto = texto.encode('ASCII', 'ignore').decode('ASCII')

        # Remove pontuacao extra
        texto = texto.replace('.', ' ').replace(',', ' ').replace('-', ' ')

        # Remove espacos multiplos
        palavras = texto.split()

        # Expandir abreviacoes (opcional - pode melhorar ou piorar o match)
        # palavras_expandidas = []
        # for palavra in palavras:
        #     palavras_expandidas.append(self.ABREVIACOES.get(palavra, palavra))
        # return ' '.join(palavras_expandidas)

        return ' '.join(palavras)

    def buscar_via(self, nome_waze: str) -> Tuple[Optional['Logradouro'], float, str]:
        """
        Busca via oficial pelo nome retornado pelo Waze

        Args:
            nome_waze: Nome da via como retornado pelo Waze

        Returns:
            tuple: (Logradouro|None, score, metodo)
                - logradouro: Objeto Logradouro encontrado ou None
                - score: Score de confianca (0-100)
                - metodo: Metodo usado para match
        """
        from ..models import Logradouro

        if not nome_waze or not nome_waze.strip():
            return None, 0, 'vazio'

        nome_waze = nome_waze.strip()

        # Remover sufixo de cidade (ex: "Av. Brasil,Rio de Janeiro" -> "Av. Brasil")
        # Waze inclui cidade no formato "Street,City"
        if ',' in nome_waze:
            partes = nome_waze.split(',')
            # Se a segunda parte parece ser uma cidade (e nao parte do nome)
            if len(partes) >= 2:
                parte_cidade = partes[-1].strip().lower()
                cidades_conhecidas = [
                    'rio de janeiro', 'niteroi', 'niterói', 'sao goncalo',
                    'são gonçalo', 'duque de caxias', 'nova iguacu', 'nova iguaçu',
                    'belford roxo', 'sao joao de meriti', 'são joão de meriti',
                    'nilopolis', 'nilópolis', 'mesquita', 'queimados', 'japeri',
                    'magé', 'mage', 'guapimirim', 'itaborai', 'itaboraí',
                    'marica', 'maricá', 'tanguá', 'tangua', 'rio bonito',
                    'seropédica', 'seropedica', 'itaguai', 'itaguaí', 'paracambi',
                ]
                if parte_cidade in cidades_conhecidas:
                    nome_waze = ','.join(partes[:-1]).strip()

        nome_normalizado = self._normalizar(nome_waze)

        # ========================================
        # 1. MATCH EXATO NO CACHE (mais rapido)
        # ========================================
        if nome_normalizado in self._cache_vias:
            return self._cache_vias[nome_normalizado], 100, 'exato_cache'

        # ========================================
        # 2. MATCH EXATO NO BANCO (case insensitive)
        # ========================================
        via_exata = Logradouro.objects.filter(
            nome_completo__iexact=nome_waze
        ).first()

        if via_exata:
            return via_exata, 100, 'exato_banco'

        # Tentar tambem com nome normalizado
        via_normalizada = Logradouro.objects.filter(
            nome_completo__iexact=nome_waze.title()
        ).first()

        if via_normalizada:
            return via_normalizada, 98, 'exato_normalizado'

        # ========================================
        # 3. FUZZY MATCH NO CACHE (vias importantes)
        # ========================================
        melhor_score = 0
        melhor_via = None
        melhor_metodo = 'nao_encontrado'

        for chave, via in self._cache_vias.items():
            # Ratio simples
            score_ratio = fuzz.ratio(nome_normalizado, chave)

            # Token set ratio (ignora ordem das palavras)
            score_token = fuzz.token_set_ratio(nome_normalizado, chave)

            # Usar o melhor score
            score = max(score_ratio, score_token)

            if score > melhor_score:
                melhor_score = score
                melhor_via = via
                melhor_metodo = 'fuzzy_cache'

        if melhor_score >= self.SCORE_MINIMO_FUZZY:
            return melhor_via, melhor_score, melhor_metodo

        # ========================================
        # 4. BUSCA PARCIAL NO BANCO (mais lento)
        # ========================================
        # Extrair primeira palavra significativa para busca inicial
        palavras = nome_normalizado.split()
        if not palavras:
            return None, 0, 'vazio'

        # Pular tipo de via para buscar pelo nome
        palavra_busca = palavras[0]
        if palavra_busca in self.ABREVIACOES or len(palavra_busca) <= 3:
            if len(palavras) > 1:
                palavra_busca = palavras[1]

        # Buscar candidatos no banco
        candidatos = Logradouro.objects.filter(
            Q(nome_completo__icontains=palavra_busca) |
            Q(nome_parcial__icontains=palavra_busca)
        )[:100]  # Limitar para performance

        for via in candidatos:
            chave_via = self._normalizar(via.nome_completo)

            # Ratio simples
            score_ratio = fuzz.ratio(nome_normalizado, chave_via)

            # Token set ratio
            score_token = fuzz.token_set_ratio(nome_normalizado, chave_via)

            # Partial ratio (bom para nomes incompletos)
            score_partial = fuzz.partial_ratio(nome_normalizado, chave_via)

            score = max(score_ratio, score_token, score_partial)

            if score > melhor_score:
                melhor_score = score
                melhor_via = via
                melhor_metodo = 'fuzzy_banco'

        if melhor_score >= self.SCORE_MINIMO_PARCIAL:
            return melhor_via, melhor_score, melhor_metodo

        # ========================================
        # 5. NAO ENCONTRADO
        # ========================================
        logger.debug(f"Via nao encontrada: '{nome_waze}' (melhor score: {melhor_score})")
        return None, melhor_score, 'nao_encontrado'

    def buscar_vias_multiplas(self, nomes: list) -> dict:
        """
        Busca multiplas vias de uma vez (otimizado para batch)

        Args:
            nomes: Lista de nomes de vias do Waze

        Returns:
            dict: {nome_waze: (logradouro, score, metodo)}
        """
        resultados = {}

        for nome in nomes:
            if nome:
                resultados[nome] = self.buscar_via(nome)

        return resultados

    def estatisticas_cache(self) -> dict:
        """Retorna estatisticas do cache"""
        return {
            'total_vias_cache': len(self._cache_vias),
            'memoria_kb': len(str(self._cache_vias)) / 1024,
        }


# Instancia singleton para reutilizacao
_matcher_instance = None


def get_via_matcher() -> ViaMatcher:
    """
    Retorna instancia singleton do ViaMatcher

    Usar esta funcao para evitar recarregar o cache multiplas vezes.
    """
    global _matcher_instance

    if _matcher_instance is None:
        _matcher_instance = ViaMatcher()

    return _matcher_instance
