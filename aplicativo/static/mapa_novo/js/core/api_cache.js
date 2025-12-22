/**
 * API Cache System - Sistema de Cache para APIs
 * IntegraCity - Reduz chamadas repetidas e melhora performance
 */

const IntegraCityCache = (function() {
    'use strict';

    // Configurações
    const CONFIG = {
        defaultTTL: 60000,        // 1 minuto padrão
        maxCacheSize: 100,        // Máximo de itens em cache
        storageKey: 'integracity_api_cache',
        enablePersistence: true,   // Salvar em localStorage
        debug: false
    };

    // TTL específico por endpoint
    const ENDPOINT_TTL = {
        '/api/estagio-atual/': 30000,      // 30 segundos - crítico
        '/api/cameras/': 120000,           // 2 minutos
        '/api/sirenes/': 60000,            // 1 minuto
        '/api/alertas/': 30000,            // 30 segundos
        '/api/ocorrencias/': 45000,        // 45 segundos
        '/api/chuva/': 60000,              // 1 minuto
        '/api/ventos/': 120000,            // 2 minutos
        '/api/pluviometros/': 60000,       // 1 minuto
        '/api/transito-status/': 60000,    // 1 minuto
        '/api/brt/': 120000,               // 2 minutos
        '/api/metro/': 120000,             // 2 minutos
        '/api/waze/': 30000,               // 30 segundos
        '/api/escolas/': 300000,           // 5 minutos - estático
        '/api/hospitais/': 300000,         // 5 minutos - estático
        '/api/bens-tombados/': 300000      // 5 minutos - estático
    };

    // Cache em memória
    let memoryCache = new Map();

    // Estatísticas
    let stats = {
        hits: 0,
        misses: 0,
        expired: 0
    };

    /**
     * Log de debug
     */
    function log(...args) {
        if (CONFIG.debug) {
            console.log('[IntegraCityCache]', ...args);
        }
    }

    /**
     * Gerar chave de cache
     */
    function generateKey(url, params = {}) {
        const sortedParams = Object.keys(params)
            .sort()
            .map(k => `${k}=${params[k]}`)
            .join('&');
        return `${url}${sortedParams ? '?' + sortedParams : ''}`;
    }

    /**
     * Obter TTL para um endpoint
     */
    function getTTL(url) {
        for (const [endpoint, ttl] of Object.entries(ENDPOINT_TTL)) {
            if (url.includes(endpoint)) {
                return ttl;
            }
        }
        return CONFIG.defaultTTL;
    }

    /**
     * Verificar se item expirou
     */
    function isExpired(item) {
        return Date.now() > item.expiry;
    }

    /**
     * Limpar itens expirados
     */
    function cleanExpired() {
        let cleaned = 0;
        for (const [key, item] of memoryCache) {
            if (isExpired(item)) {
                memoryCache.delete(key);
                cleaned++;
            }
        }
        if (cleaned > 0) {
            log(`Limpou ${cleaned} itens expirados`);
            stats.expired += cleaned;
        }
    }

    /**
     * Limitar tamanho do cache (LRU)
     */
    function enforceMaxSize() {
        if (memoryCache.size > CONFIG.maxCacheSize) {
            const keysToDelete = Array.from(memoryCache.keys())
                .slice(0, memoryCache.size - CONFIG.maxCacheSize);
            keysToDelete.forEach(key => memoryCache.delete(key));
            log(`Removeu ${keysToDelete.length} itens (LRU)`);
        }
    }

    /**
     * Obter do cache
     */
    function get(url, params = {}) {
        const key = generateKey(url, params);
        const item = memoryCache.get(key);

        if (!item) {
            stats.misses++;
            log('MISS:', key);
            return null;
        }

        if (isExpired(item)) {
            memoryCache.delete(key);
            stats.misses++;
            log('EXPIRED:', key);
            return null;
        }

        stats.hits++;
        log('HIT:', key);

        // Mover para o final (LRU)
        memoryCache.delete(key);
        memoryCache.set(key, item);

        return item.data;
    }

    /**
     * Salvar no cache
     */
    function set(url, data, params = {}, customTTL = null) {
        const key = generateKey(url, params);
        const ttl = customTTL || getTTL(url);

        const item = {
            data: data,
            expiry: Date.now() + ttl,
            timestamp: Date.now()
        };

        memoryCache.set(key, item);
        enforceMaxSize();

        log('SET:', key, `TTL: ${ttl}ms`);

        // Persistir em localStorage se habilitado
        if (CONFIG.enablePersistence) {
            persistToStorage();
        }
    }

    /**
     * Invalidar cache para URL
     */
    function invalidate(url) {
        let invalidated = 0;
        for (const key of memoryCache.keys()) {
            if (key.includes(url)) {
                memoryCache.delete(key);
                invalidated++;
            }
        }
        log(`Invalidou ${invalidated} itens para: ${url}`);
        return invalidated;
    }

    /**
     * Limpar todo o cache
     */
    function clear() {
        memoryCache.clear();
        if (CONFIG.enablePersistence) {
            localStorage.removeItem(CONFIG.storageKey);
        }
        log('Cache limpo completamente');
    }

    /**
     * Persistir em localStorage
     */
    function persistToStorage() {
        try {
            const serializable = {};
            for (const [key, item] of memoryCache) {
                serializable[key] = item;
            }
            localStorage.setItem(CONFIG.storageKey, JSON.stringify(serializable));
        } catch (e) {
            log('Erro ao persistir cache:', e);
        }
    }

    /**
     * Restaurar do localStorage
     */
    function restoreFromStorage() {
        try {
            const stored = localStorage.getItem(CONFIG.storageKey);
            if (stored) {
                const parsed = JSON.parse(stored);
                for (const [key, item] of Object.entries(parsed)) {
                    if (!isExpired(item)) {
                        memoryCache.set(key, item);
                    }
                }
                log(`Restaurou ${memoryCache.size} itens do storage`);
            }
        } catch (e) {
            log('Erro ao restaurar cache:', e);
        }
    }

    /**
     * Fetch com cache
     */
    async function cachedFetch(url, options = {}) {
        const {
            params = {},
            bypassCache = false,
            ttl = null,
            showLoading = true
        } = options;

        // Verificar cache primeiro
        if (!bypassCache) {
            const cached = get(url, params);
            if (cached) {
                return { data: cached, fromCache: true };
            }
        }

        // Fazer requisição
        try {
            const fullUrl = params && Object.keys(params).length
                ? `${url}?${new URLSearchParams(params)}`
                : url;

            const response = await fetch(fullUrl, {
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            // Salvar no cache
            set(url, data, params, ttl);

            return { data: data, fromCache: false };
        } catch (error) {
            log('Fetch error:', url, error);
            throw error;
        }
    }

    /**
     * Obter estatísticas
     */
    function getStats() {
        const total = stats.hits + stats.misses;
        return {
            ...stats,
            total: total,
            hitRate: total > 0 ? ((stats.hits / total) * 100).toFixed(1) + '%' : '0%',
            cacheSize: memoryCache.size
        };
    }

    /**
     * Pre-fetch de dados importantes
     */
    async function prefetch(urls) {
        log('Prefetching:', urls.length, 'URLs');
        const promises = urls.map(url =>
            cachedFetch(url).catch(e => log('Prefetch falhou:', url))
        );
        await Promise.allSettled(promises);
    }

    // Inicialização
    function init() {
        restoreFromStorage();

        // Limpar expirados periodicamente
        setInterval(cleanExpired, 30000);

        log('Cache inicializado');
    }

    // Inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // API Pública
    return {
        get,
        set,
        invalidate,
        clear,
        cachedFetch,
        getStats,
        prefetch,
        setDebug: (enabled) => { CONFIG.debug = enabled; }
    };
})();

// Expor globalmente
window.IntegraCityCache = IntegraCityCache;

console.log('✅ api_cache.js carregado');
