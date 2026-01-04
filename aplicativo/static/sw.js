/**
 * Service Worker - IntegraCity PWA
 * Versao: 1.0.0
 */

const CACHE_NAME = 'integracity-cache-v1';
const RUNTIME_CACHE = 'integracity-runtime-v1';

// Arquivos para cache estático
const STATIC_ASSETS = [
    '/integracity/',
    '/integracity/login/',
    '/integracity/static/mapa_novo/css/cor_design_system.css',
    '/integracity/static/mapa_novo/css/cor_components.css',
    '/integracity/static/mapa_novo/css/cor_navbar.css',
    '/integracity/static/mapa_novo/css/dark_mode.css',
    '/integracity/static/mapa_novo/css/loading_states.css',
    '/integracity/static/mapa_novo/css/mobile_responsive.css',
    '/integracity/static/mapa_novo/js/core/api_cache.js',
    '/integracity/static/mapa_novo/js/features/theme_toggle.js',
    '/integracity/static/mapa_novo/js/features/realtime_notifications.js',
    '/integracity/static/images/RIOPREFEITURA_COR_horizontal_azul.png',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css',
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css',
    'https://code.jquery.com/jquery-3.6.0.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js'
];

// URLs para cache de API (com estratégia network-first)
const API_ROUTES = [
    '/integracity/api/estagio-atual/',
    '/integracity/api/cameras/',
    '/integracity/api/sirenes/',
    '/integracity/api/alertas/',
    '/integracity/api/chuva/',
    '/integracity/api/ocorrencias/'
];

/**
 * Instalação do Service Worker
 */
self.addEventListener('install', (event) => {
    console.log('[SW] Instalando Service Worker...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Cacheando arquivos estáticos...');
                return cache.addAll(STATIC_ASSETS.map(url => {
                    return new Request(url, { mode: 'cors' });
                })).catch(err => {
                    console.warn('[SW] Alguns arquivos não puderam ser cacheados:', err);
                });
            })
            .then(() => {
                console.log('[SW] Instalação completa!');
                return self.skipWaiting();
            })
    );
});

/**
 * Ativação do Service Worker
 */
self.addEventListener('activate', (event) => {
    console.log('[SW] Ativando Service Worker...');

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== CACHE_NAME && name !== RUNTIME_CACHE)
                        .map((name) => {
                            console.log('[SW] Removendo cache antigo:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('[SW] Ativação completa!');
                return self.clients.claim();
            })
    );
});

/**
 * Interceptação de requisições
 */
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Ignorar requisições não-GET
    if (request.method !== 'GET') {
        return;
    }

    // Ignorar extensões do navegador
    if (url.protocol === 'chrome-extension:') {
        return;
    }

    // Estratégia para APIs: Network First com fallback para cache
    if (API_ROUTES.some(route => url.pathname.includes(route))) {
        event.respondWith(networkFirst(request));
        return;
    }

    // Estratégia para arquivos estáticos: Cache First com fallback para network
    if (isStaticAsset(url)) {
        event.respondWith(cacheFirst(request));
        return;
    }

    // Páginas HTML: Network First
    if (request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // Default: Network com fallback para cache
    event.respondWith(networkFirst(request));
});

/**
 * Verificar se é arquivo estático
 */
function isStaticAsset(url) {
    const extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf'];
    return extensions.some(ext => url.pathname.endsWith(ext));
}

/**
 * Estratégia: Cache First
 */
async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        // Atualizar cache em background
        updateCache(request);
        return cachedResponse;
    }

    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.warn('[SW] Falha ao buscar:', request.url);
        return new Response('Offline', { status: 503 });
    }
}

/**
 * Estratégia: Network First
 */
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);

        if (networkResponse.ok) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        const cachedResponse = await caches.match(request);

        if (cachedResponse) {
            console.log('[SW] Servindo do cache (offline):', request.url);
            return cachedResponse;
        }

        // Retornar página offline para navegação
        if (request.headers.get('accept')?.includes('text/html')) {
            return caches.match('/integracity/offline/') || new Response(
                `<!DOCTYPE html>
                <html lang="pt-BR">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>IntegraCity - Offline</title>
                    <style>
                        body {
                            font-family: -apple-system, system-ui, sans-serif;
                            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                            color: #f1f5f9;
                            min-height: 100vh;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            margin: 0;
                            text-align: center;
                        }
                        .container {
                            padding: 40px;
                        }
                        h1 { font-size: 48px; margin-bottom: 16px; }
                        p { color: #94a3b8; font-size: 18px; margin-bottom: 24px; }
                        .btn {
                            background: #3b82f6;
                            color: white;
                            padding: 12px 24px;
                            border: none;
                            border-radius: 8px;
                            font-size: 16px;
                            cursor: pointer;
                        }
                        .btn:hover { background: #2563eb; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>📡</h1>
                        <h2>Você está offline</h2>
                        <p>Verifique sua conexão com a internet e tente novamente.</p>
                        <button class="btn" onclick="location.reload()">Tentar novamente</button>
                    </div>
                </body>
                </html>`,
                { headers: { 'Content-Type': 'text/html' } }
            );
        }

        // Retornar erro para APIs
        return new Response(
            JSON.stringify({ error: 'Offline', message: 'Sem conexão com a internet' }),
            { status: 503, headers: { 'Content-Type': 'application/json' } }
        );
    }
}

/**
 * Atualizar cache em background
 */
async function updateCache(request) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response);
        }
    } catch (error) {
        // Silenciar erros de atualização em background
    }
}

/**
 * Notificações Push
 */
self.addEventListener('push', (event) => {
    if (!event.data) return;

    try {
        const data = event.data.json();

        const options = {
            body: data.body || data.message,
            icon: '/integracity/static/images/integracity-icon-192.png',
            badge: '/integracity/static/images/integracity-badge.png',
            vibrate: [100, 50, 100],
            data: {
                url: data.url || '/integracity/cor/',
                timestamp: Date.now()
            },
            actions: [
                { action: 'open', title: 'Abrir' },
                { action: 'dismiss', title: 'Dispensar' }
            ]
        };

        event.waitUntil(
            self.registration.showNotification(data.title || 'IntegraCity', options)
        );
    } catch (error) {
        console.error('[SW] Erro ao processar notificação push:', error);
    }
});

/**
 * Clique em notificação
 */
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'dismiss') {
        return;
    }

    const url = event.notification.data?.url || '/integracity/cor/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Tentar focar em janela existente
                for (const client of clientList) {
                    if (client.url.includes('/integracity/') && 'focus' in client) {
                        client.navigate(url);
                        return client.focus();
                    }
                }
                // Abrir nova janela
                return clients.openWindow(url);
            })
    );
});

/**
 * Sincronização em background
 */
self.addEventListener('sync', (event) => {
    console.log('[SW] Sync event:', event.tag);

    if (event.tag === 'sync-data') {
        event.waitUntil(syncData());
    }
});

async function syncData() {
    console.log('[SW] Sincronizando dados...');
    // Implementar sincronização de dados offline quando necessário
}

console.log('[SW] Service Worker carregado');
