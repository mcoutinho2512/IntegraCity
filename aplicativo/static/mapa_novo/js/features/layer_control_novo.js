/**
 * layer_control_novo.js - Sistema Unificado de Controle de Camadas
 * Gerencia a visibilidade das camadas no mapa usando o painel do HTML
 */

// Estado das camadas
let layerStatesNovo = {
    sirenes: true,
    eventos: true,
    ocorrencias: true,
    pluviometros: true,
    ventos: true,
    bolsoes: true,
    escolas: true,
    bensTombados: true,
    cameras: true,
    wazeAlertas: true,
    wazeJams: true
};

/**
 * Inicializa o sistema de controle de camadas
 * Conecta os checkboxes do HTML com as camadas do mapa
 */
function initLayerControl() {
    console.log('🗺️ Inicializando controle de camadas...');

    // Aguardar mapa e markers estarem prontos
    const checkReady = setInterval(() => {
        if (typeof map !== 'undefined' && typeof markers !== 'undefined' && markers.sirenes) {
            clearInterval(checkReady);
            setupLayerControlSystem();
        }
    }, 500);
}

function setupLayerControlSystem() {
    console.log('✅ Mapa e markers prontos, configurando toggles...');

    // Configurar todos os checkboxes com data-toggle
    const toggles = document.querySelectorAll('[data-toggle]');

    toggles.forEach(toggle => {
        const layerName = toggle.getAttribute('data-toggle');

        // Sincronizar estado inicial do checkbox com o estado da camada
        if (markers[layerName]) {
            toggle.checked = map.hasLayer(markers[layerName]);
            layerStatesNovo[layerName] = toggle.checked;
        }

        // Adicionar event listener
        toggle.addEventListener('change', function() {
            toggleLayerNovo(layerName, this.checked);
        });
    });

    // Atualizar contagens iniciais
    setTimeout(updateLayerCountsNovo, 1000);

    console.log('✅ Sistema de camadas configurado com sucesso!');
}

/**
 * Alterna a visibilidade de uma camada no mapa
 */
function toggleLayerNovo(layerName, isVisible) {
    // Atualizar estado
    layerStatesNovo[layerName] = isVisible;

    console.log(`🔄 Toggle ${layerName}: ${isVisible ? 'ON' : 'OFF'}`);

    // Verificar se mapa e markers existem
    if (typeof map === 'undefined' || !markers) {
        console.warn('⏳ Aguardando mapa/markers serem inicializados...');
        return;
    }

    // Verificar se a camada existe
    if (!markers[layerName]) {
        console.warn(`⚠️ Camada "${layerName}" não encontrada em markers`);
        return;
    }

    // Adicionar ou remover camada do mapa
    if (isVisible) {
        if (!map.hasLayer(markers[layerName])) {
            map.addLayer(markers[layerName]);
            console.log(`✅ Camada ${layerName} adicionada ao mapa`);
        }
    } else {
        if (map.hasLayer(markers[layerName])) {
            map.removeLayer(markers[layerName]);
            console.log(`❌ Camada ${layerName} removida do mapa`);
        }
    }

    // Toggle camadas Waze (armazenadas em window)
    if (layerName === 'wazeAlertas' && window.wazeAlertasLayer) {
        if (isVisible) {
            if (!map.hasLayer(window.wazeAlertasLayer)) {
                map.addLayer(window.wazeAlertasLayer);
            }
        } else {
            if (map.hasLayer(window.wazeAlertasLayer)) {
                map.removeLayer(window.wazeAlertasLayer);
            }
        }
    }

    if (layerName === 'wazeJams' && window.wazeJamsLayer) {
        if (isVisible) {
            if (!map.hasLayer(window.wazeJamsLayer)) {
                map.addLayer(window.wazeJamsLayer);
            }
        } else {
            if (map.hasLayer(window.wazeJamsLayer)) {
                map.removeLayer(window.wazeJamsLayer);
            }
        }
    }

    // Atualizar contagens
    updateLayerCountsNovo();
}


/**
 * Atualiza as contagens de marcadores em cada camada
 */
function updateLayerCountsNovo() {
    if (typeof markers === 'undefined' || !markers.sirenes) return;

    const layerNames = ['sirenes', 'eventos', 'ocorrencias', 'pluviometros', 'ventos', 'bolsoes', 'escolas', 'bensTombados', 'cameras'];

    layerNames.forEach(name => {
        if (markers[name]) {
            const count = markers[name].getLayers().length;

            // Atualizar elementos com data-count
            const countEl = document.querySelector(`[data-count="${name}"]`);
            if (countEl) {
                countEl.textContent = count;
            }
        }
    });

    // Atualizar contagens do Waze
    if (window.wazeAlertasLayer) {
        const alertasCount = window.wazeAlertasLayer.getLayers().length;
        const wazeAlertasEl = document.querySelector('[data-count="wazeAlertas"]');
        if (wazeAlertasEl) {
            wazeAlertasEl.textContent = alertasCount;
        }
    }

    if (window.wazeJamsLayer) {
        const jamsCount = window.wazeJamsLayer.getLayers().length;
        const wazeJamsEl = document.querySelector('[data-count="wazeJams"]');
        if (wazeJamsEl) {
            wazeJamsEl.textContent = jamsCount;
        }
    }
}

/**
 * Toggle do painel de camadas
 */
function toggleLayerPanel() {
    const panel = document.getElementById('layer-panel');
    if (panel) {
        panel.classList.toggle('collapsed');
    }
}

// Inicializar quando DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLayerControl);
} else {
    initLayerControl();
}

// Conectar botão externo ao toggle do painel
document.addEventListener('DOMContentLoaded', () => {
    const layersBtn = document.getElementById('layers-toggle');
    if (layersBtn) {
        layersBtn.addEventListener('click', toggleLayerPanel);
        console.log('✅ Botão de camadas conectado');
    }
});

// Atualizar contagens periodicamente
setInterval(() => {
    if (typeof markers !== 'undefined') {
        updateLayerCountsNovo();
    }
}, 5000);

console.log('✅ layer_control_novo.js carregado');