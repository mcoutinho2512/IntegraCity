/**
 * Gerenciador de Thumbnails ao Vivo - IntegraCity
 * Limita a 8 streams simultaneos por performance
 *
 * Uso:
 * const manager = new ThumbnailManager();
 * manager.init();
 */

class ThumbnailManager {
    constructor(options = {}) {
        this.maxLiveStreams = options.maxStreams || 5;  // LIMITE FIXO - 5 cameras por pagina
        this.activeStreams = new Map();  // cameraId -> videoElement
        this.visibleCards = new Set();
        this.observer = null;
        this.scrollDebounceTimer = null;
        this.isInitialized = false;

        // Configuracoes de stream
        this.streamBaseUrl = '/integracity/api/camera/';
        this.streamSuffix = '/stream/?embed=1';
    }

    init() {
        if (this.isInitialized) {
            console.warn('ThumbnailManager ja inicializado');
            return;
        }

        console.log(`ThumbnailManager inicializado (max ${this.maxLiveStreams} streams)`);

        this.initIntersectionObserver();
        this.setupScrollListener();
        this.isInitialized = true;

        // Primeira atualizacao apos pequeno delay
        setTimeout(() => this.updateVisibleStreams(), 500);
    }

    initIntersectionObserver() {
        const options = {
            root: null,
            rootMargin: '100px',
            threshold: 0.1
        };

        this.observer = new IntersectionObserver((entries) => {
            let hasChanges = false;

            entries.forEach(entry => {
                const cameraId = entry.target.dataset.cameraId;
                if (!cameraId) return;

                if (entry.isIntersecting) {
                    if (!this.visibleCards.has(cameraId)) {
                        this.visibleCards.add(cameraId);
                        hasChanges = true;
                    }
                } else {
                    if (this.visibleCards.has(cameraId)) {
                        this.visibleCards.delete(cameraId);
                        hasChanges = true;
                    }
                }
            });

            if (hasChanges) {
                this.scheduleUpdate();
            }
        }, options);

        // Observar cards existentes
        this.observeAllCards();
    }

    observeAllCards() {
        document.querySelectorAll('.video-camera-card[data-camera-id]').forEach(card => {
            this.observer.observe(card);
        });
    }

    // Chamar apos adicionar novos cards ao DOM
    observeNewCards() {
        this.observeAllCards();
        this.scheduleUpdate();
    }

    setupScrollListener() {
        window.addEventListener('scroll', () => {
            this.scheduleUpdate();
        }, { passive: true });

        // Tambem reagir a resize
        window.addEventListener('resize', () => {
            this.scheduleUpdate();
        }, { passive: true });
    }

    scheduleUpdate() {
        clearTimeout(this.scrollDebounceTimer);
        this.scrollDebounceTimer = setTimeout(() => {
            this.updateVisibleStreams();
        }, 200);
    }

    updateVisibleStreams() {
        // Pegar todos os cards visiveis ordenados por posicao na tela
        const visibleCardElements = Array.from(document.querySelectorAll('.video-camera-card[data-camera-id]'))
            .filter(card => this.isElementVisible(card))
            .sort((a, b) => {
                const rectA = a.getBoundingClientRect();
                const rectB = b.getBoundingClientRect();
                return rectA.top - rectB.top;
            });

        // IDs das primeiras N cameras visiveis
        const topVisibleIds = new Set(
            visibleCardElements
                .slice(0, this.maxLiveStreams)
                .map(card => card.dataset.cameraId)
        );

        // Parar streams que nao estao mais entre as top N
        this.activeStreams.forEach((data, cameraId) => {
            if (!topVisibleIds.has(cameraId)) {
                this.stopStream(cameraId);
            }
        });

        // Iniciar streams das top N que ainda nao estao ativos
        visibleCardElements.slice(0, this.maxLiveStreams).forEach(card => {
            const cameraId = card.dataset.cameraId;
            if (!this.activeStreams.has(cameraId)) {
                this.startStream(card);
            }
        });

        // Log
        console.log(`Streams ativos: ${this.activeStreams.size}/${this.maxLiveStreams}`);
    }

    isElementVisible(element) {
        const rect = element.getBoundingClientRect();
        const windowHeight = window.innerHeight || document.documentElement.clientHeight;

        return (
            rect.top < windowHeight + 100 &&
            rect.bottom > -100
        );
    }

    startStream(card) {
        const cameraId = card.dataset.cameraId;
        if (!cameraId || this.activeStreams.has(cameraId)) {
            return;
        }

        // Verificar limite
        if (this.activeStreams.size >= this.maxLiveStreams) {
            return;
        }

        const thumbnail = card.querySelector('.video-camera-thumbnail');
        if (!thumbnail) return;

        // Formatar ID para 6 digitos (padrao TIXXI)
        const cameraIdPadded = String(cameraId).padStart(6, '0');
        const streamUrl = `${this.streamBaseUrl}${cameraIdPadded}${this.streamSuffix}`;

        // Criar iframe para stream
        const iframe = document.createElement('iframe');
        iframe.className = 'thumbnail-stream';
        iframe.src = streamUrl;
        iframe.setAttribute('allowfullscreen', '');
        iframe.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: none;
            z-index: 1;
        `;

        // Esconder placeholder
        const placeholder = thumbnail.querySelector('.video-camera-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }

        // Adicionar indicador de ao vivo
        let liveIndicator = thumbnail.querySelector('.live-indicator');
        if (!liveIndicator) {
            liveIndicator = document.createElement('div');
            liveIndicator.className = 'live-indicator';
            liveIndicator.innerHTML = '<span class="live-dot"></span>AO VIVO';
            thumbnail.appendChild(liveIndicator);
        }
        liveIndicator.style.display = 'flex';

        // Adicionar iframe
        thumbnail.appendChild(iframe);

        // Salvar referencia
        this.activeStreams.set(cameraId, {
            iframe: iframe,
            card: card
        });

        console.log(`Stream iniciado: ${cameraId}`);
    }

    stopStream(cameraId) {
        const data = this.activeStreams.get(cameraId);
        if (!data) return;

        // Remover iframe
        if (data.iframe && data.iframe.parentNode) {
            data.iframe.src = '';
            data.iframe.parentNode.removeChild(data.iframe);
        }

        // Mostrar placeholder
        const thumbnail = data.card.querySelector('.video-camera-thumbnail');
        if (thumbnail) {
            const placeholder = thumbnail.querySelector('.video-camera-placeholder');
            if (placeholder) {
                placeholder.style.display = 'flex';
            }

            // Esconder indicador ao vivo
            const liveIndicator = thumbnail.querySelector('.live-indicator');
            if (liveIndicator) {
                liveIndicator.style.display = 'none';
            }
        }

        this.activeStreams.delete(cameraId);
        console.log(`Stream parado: ${cameraId}`);
    }

    stopAllStreams() {
        this.activeStreams.forEach((data, cameraId) => {
            this.stopStream(cameraId);
        });
    }

    destroy() {
        console.log('ThumbnailManager destruido');

        this.stopAllStreams();

        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }

        clearTimeout(this.scrollDebounceTimer);
        this.visibleCards.clear();
        this.isInitialized = false;
    }

    // Metodo para recarregar apos mudanca de pagina/filtro
    refresh() {
        this.stopAllStreams();
        this.visibleCards.clear();

        // Re-observar cards
        setTimeout(() => {
            this.observeAllCards();
            this.updateVisibleStreams();
        }, 100);
    }
}

// CSS adicional para thumbnails
const thumbnailStyles = `
<style id="thumbnail-manager-styles">
.video-camera-thumbnail {
    position: relative;
    width: 100%;
    padding-top: 56.25%; /* 16:9 */
    background: #0a0a0f;
    overflow: hidden;
}

.video-camera-thumbnail .video-camera-placeholder {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #0a0a0f, #1a1a24);
    font-size: 48px;
    color: #00D4FF;
    opacity: 0.5;
}

.video-camera-thumbnail .thumbnail-stream {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: none;
    z-index: 1;
    pointer-events: none;
}

.video-camera-thumbnail .live-indicator {
    position: absolute;
    top: 10px;
    left: 10px;
    background: rgba(255, 0, 85, 0.9);
    color: #fff;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 6px;
    z-index: 10;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.video-camera-thumbnail .live-dot {
    width: 8px;
    height: 8px;
    background: #fff;
    border-radius: 50%;
    animation: livePulse 1.5s ease-in-out infinite;
}

@keyframes livePulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
}
</style>
`;

// Injetar estilos
if (!document.getElementById('thumbnail-manager-styles')) {
    document.head.insertAdjacentHTML('beforeend', thumbnailStyles);
}

// Exportar classe para uso global
window.ThumbnailManager = ThumbnailManager;

console.log('cameras_thumbnails.js carregado - ThumbnailManager disponivel');
