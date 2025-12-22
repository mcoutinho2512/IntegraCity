/**
 * layer_control.js - Controle de Camadas
 */

let layerStates = {
    sirenes: true,
    eventos: true,
    ocorrencias: true,
    pluviometros: true,
    ventos: true
};

function createLayerControlPanel() {
    const panel = document.createElement('div');
    panel.className = 'layer-control-panel';
    panel.innerHTML = `
        <div class="panel-header">
            <i class="bi bi-layers-fill"></i>
            <h3>Camadas do Mapa</h3>
        </div>
        
        <div class="layer-item" onclick="toggleLayer('sirenes')">
            <div class="layer-info">
                <div class="layer-icon icon-sirene">
                    <i class="bi bi-megaphone-fill"></i>
                </div>
                <div class="layer-details">
                    <div class="layer-name">Sirenes</div>
                    <div class="layer-count" id="count-sirenes">0 ativos</div>
                </div>
            </div>
            <div class="layer-toggle active" id="toggle-sirenes"></div>
        </div>
        
        <div class="layer-item" onclick="toggleLayer('eventos')">
            <div class="layer-info">
                <div class="layer-icon icon-evento">
                    <i class="bi bi-calendar-event-fill"></i>
                </div>
                <div class="layer-details">
                    <div class="layer-name">Eventos</div>
                    <div class="layer-count" id="count-eventos">0 programados</div>
                </div>
            </div>
            <div class="layer-toggle active" id="toggle-eventos"></div>
        </div>
        
        <div class="layer-item" onclick="toggleLayer('ocorrencias')">
            <div class="layer-info">
                <div class="layer-icon icon-ocorrencia">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                </div>
                <div class="layer-details">
                    <div class="layer-name">Ocorrencias</div>
                    <div class="layer-count" id="count-ocorrencias">0 abertas</div>
                </div>
            </div>
            <div class="layer-toggle active" id="toggle-ocorrencias"></div>
        </div>

        <div class="layer-item" onclick="toggleLayer('pluviometros')">
            <div class="layer-info">
                <div class="layer-icon icon-pluviometro" style="background: #3b82f6;">
                    <i class="bi bi-cloud-rain-fill"></i>
                </div>
                <div class="layer-details">
                    <div class="layer-name">Pluviômetros</div>
                    <div class="layer-count" id="count-pluviometros">0 estações</div>
                </div>
            </div>
            <div class="layer-toggle active" id="toggle-pluviometros"></div>
        </div>
        
        <div class="estagio-badge estagio-normalidade" id="estagio-display">
            Carregando estagio...
        </div>

<div class="layer-item" onclick="toggleLayer('ventos')">
    <div class="layer-info">
        <div class="layer-icon" style="background: #10b981;">
            <i class="bi bi-wind"></i>
        </div>
        <div class="layer-details">
            <div class="layer-name">Estações de Vento</div>
            <div class="layer-count" id="count-ventos">0 estações</div>
        </div>
    </div>
    <div class="layer-toggle active" id="toggle-ventos"></div>
</div>


    `;
    
    document.body.appendChild(panel);
    carregarEstagio();
}

function toggleLayer(layerName) {
    layerStates[layerName] = !layerStates[layerName];
    
    const toggle = document.getElementById('toggle-' + layerName);
    toggle.classList.toggle('active');
    
    if (layerStates[layerName]) {
        map.addLayer(markers[layerName]);
    } else {
        map.removeLayer(markers[layerName]);
    }
}

function updateLayerCounts() {
    const counts = {
        sirenes: markers.sirenes ? markers.sirenes.getLayers().length : 0,
        eventos: markers.eventos ? markers.eventos.getLayers().length : 0,
        ocorrencias: markers.ocorrencias ? markers.ocorrencias.getLayers().length : 0,
        pluviometros: markers.pluviometros ? markers.pluviometros.getLayers().length : 0,
        ventos: markers.ventos ? markers.ventos.getLayers().length : 0,
    };
    
    document.getElementById('count-sirenes').textContent = counts.sirenes + ' ativos';
    document.getElementById('count-eventos').textContent = counts.eventos + ' programados';
    document.getElementById('count-ocorrencias').textContent = counts.ocorrencias + ' abertas';
    document.getElementById('count-pluviometros').textContent = counts.pluviometros + ' estações';
    document.getElementById('count-ventos').textContent = counts.ventos + ' estações';
}
async function carregarEstagio() {
    try {
        const response = await fetch('/api/estagio/');
        const data = await response.json();
        
        const estagioEl = document.getElementById('estagio-display');
        estagioEl.textContent = 'RIO: ' + data.estagio.toUpperCase();
        estagioEl.className = 'estagio-badge estagio-' + data.estagio.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    } catch (error) {
        console.error('Erro ao carregar estagio:', error);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createLayerControlPanel);
} else {
    createLayerControlPanel();
}

console.log('layer_control.js carregado');