// ============================================
// SISTEMA DE RESIZE AUTOMÁTICO DO MAPA
// ============================================

(function() {
    console.log('🗺️ Configurando resize automático do mapa...');

    // Função para invalidar tamanho do mapa
    function invalidateMapSize() {
        if (window.map) {
            setTimeout(() => {
                map.invalidateSize({
                    pan: false,
                    animate: true
                });
                console.log('✅ Mapa redimensionado');
            }, 300);
        }
    }

    // ============================================
    // 1. OBSERVER PARA O CONTAINER DO MAPA
    // ============================================
    const mapContainer = document.getElementById('map');
    
    if (mapContainer) {
        const resizeObserver = new ResizeObserver(entries => {
            for (let entry of entries) {
                invalidateMapSize();
            }
        });
        
        resizeObserver.observe(mapContainer);
        console.log('✅ ResizeObserver configurado no #map');
    }

    // ============================================
    // 2. OBSERVER PARA O PAINEL DE MONITORAMENTO
    // ============================================
    const monitoringPanel = document.getElementById('monitoring-panel');
    
    if (monitoringPanel) {
        const panelObserver = new ResizeObserver(entries => {
            invalidateMapSize();
        });
        
        panelObserver.observe(monitoringPanel);
        console.log('✅ ResizeObserver configurado no painel de monitoramento');

        // Detectar mudanças de classe (collapsed/expanded)
        const panelClassObserver = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    console.log('🔄 Painel mudou de estado');
                    invalidateMapSize();
                }
            });
        });

        panelClassObserver.observe(monitoringPanel, {
            attributes: true,
            attributeFilter: ['class']
        });
        
        console.log('✅ MutationObserver configurado para classes do painel');
    }

    // ============================================
    // 3. LISTENER NO BOTÃO DE TOGGLE
    // ============================================
    const toggleButton = document.getElementById('monitoring-toggle');
    
    if (toggleButton) {
        toggleButton.addEventListener('click', () => {
            console.log('🔘 Botão de toggle clicado');
            setTimeout(() => invalidateMapSize(), 400);
        });
        console.log('✅ Listener adicionado no botão de toggle');
    }

    // ============================================
    // 4. DETECTAR CLIQUES EM BOTÕES DE FECHAR
    // ============================================
    document.addEventListener('click', (e) => {
        const closingElement = e.target.closest('[data-bs-dismiss="modal"]') ||
                              e.target.closest('.close') ||
                              e.target.closest('.btn-close') ||
                              e.target.closest('[onclick*="close"]') ||
                              e.target.closest('[onclick*="toggle"]');
        
        if (closingElement) {
            console.log('🔘 Botão de fechar/toggle clicado');
            setTimeout(() => invalidateMapSize(), 400);
        }
    });

    // ============================================
    // 5. RESIZE DA JANELA
    // ============================================
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            console.log('🪟 Janela redimensionada');
            invalidateMapSize();
        }, 200);
    });

    // ============================================
    // 6. INVALIDAR QUANDO MAPA ESTIVER PRONTO
    // ============================================
    if (window.map) {
        setTimeout(() => {
            invalidateMapSize();
            console.log('✅ Resize inicial aplicado');
        }, 1000);
    } else {
        // Esperar mapa ser criado
        const checkMap = setInterval(() => {
            if (window.map) {
                clearInterval(checkMap);
                setTimeout(() => {
                    invalidateMapSize();
                    console.log('✅ Resize inicial aplicado (após criação)');
                }, 1000);
            }
        }, 100);
    }

    console.log('✅ Sistema de resize automático configurado!');
})();