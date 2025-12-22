/**
 * layer_control_novo.js - Painel de Camadas Retrátil
 */

// Remover botões antigos duplicados
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        // Remover todos os botões de camadas EXCETO o nosso
        const botoes = document.querySelectorAll('button');
        botoes.forEach(btn => {
            // Se é botão de camadas MAS NÃO é o novo
            if (btn.id !== 'layers-toggle' && 
                btn !== document.querySelector('.cor-layers-toggle') &&
                (btn.innerHTML.includes('layers') || 
                 btn.querySelector('.bi-layers-fill') ||
                 btn.style.borderRadius === '50%' && 
                 btn.offsetWidth === 56 &&
                 !btn.classList.contains('cor-layers-toggle'))) {
                console.log('🗑️ Removendo botão antigo:', btn);
                btn.remove();
            }
        });
    }, 1000);
});

let layerStatesNovo = {
    sirenes: true,
    eventos: true,
    ocorrencias: true,
    pluviometros: true,
    ventos: true,
    escolas: true,
    bensTombados: true,
    wazeAlertas: true,
    wazeJams: true
};

let isPanelCollapsed = false;

function createLayerControlNovo() {
    const panel = document.createElement('div');
    panel.className = 'layer-control-panel-novo';
    panel.id = 'layer-control-novo';
    panel.innerHTML = `
       <button class="layer-toggle-button" onclick="togglePanel()" title="Camadas do Mapa">
    <i class="bi bi-chevron-right"></i>
</button>
        
        <div class="layer-control-content">
            <div class="layer-control-header">
                <div class="layer-control-title">
                    <i class="bi bi-layers-fill"></i>
                    Camadas do Mapa
                </div>
            </div>
            
            <div class="layer-control-body">
                <div class="layer-group">
                    <div class="layer-group-title">
                        <i class="bi bi-activity"></i>
                        Monitoramento
                    </div>
                    
                    <div class="layer-item-novo" onclick="toggleLayerNovo('sirenes')">
                        <div class="layer-item-info">
                            <div class="layer-item-icon" style="background: #ef4444;">
                                <i class="bi bi-megaphone-fill"></i>
                            </div>
                            <div class="layer-item-details">
                                <div class="layer-item-name">Sirenes</div>
                                <div class="layer-item-count" id="count-sirenes-novo">0 ativos</div>
                            </div>
                        </div>
                        <div class="layer-item-toggle active" id="toggle-sirenes-novo"></div>
                    </div>
                    
                    <div class="layer-item-novo" onclick="toggleLayerNovo('eventos')">
                        <div class="layer-item-info">
                            <div class="layer-item-icon" style="background: #f97316;">
                                <i class="bi bi-calendar-event-fill"></i>
                            </div>
                            <div class="layer-item-details">
                                <div class="layer-item-name">Eventos</div>
                                <div class="layer-item-count" id="count-eventos-novo">0 programados</div>
                            </div>
                        </div>
                        <div class="layer-item-toggle active" id="toggle-eventos-novo"></div>
                    </div>
                    
                    <div class="layer-item-novo" onclick="toggleLayerNovo('ocorrencias')">
                        <div class="layer-item-info">
                            <div class="layer-item-icon" style="background: #eab308;">
                                <i class="bi bi-exclamation-triangle-fill"></i>
                            </div>
                            <div class="layer-item-details">
                                <div class="layer-item-name">Ocorrências</div>
                                <div class="layer-item-count" id="count-ocorrencias-novo">0 abertas</div>
                            </div>
                        </div>
                        <div class="layer-item-toggle active" id="toggle-ocorrencias-novo"></div>
                    </div>
                    
                    <div class="layer-item-novo" onclick="toggleLayerNovo('pluviometros')">
                        <div class="layer-item-info">
                            <div class="layer-item-icon" style="background: #3b82f6;">
                                <i class="bi bi-cloud-rain-fill"></i>
                            </div>
                            <div class="layer-item-details">
                                <div class="layer-item-name">Pluviômetros</div>
                                <div class="layer-item-count" id="count-pluviometros-novo">0 estações</div>
                            </div>
                        </div>
                        <div class="layer-item-toggle active" id="toggle-pluviometros-novo"></div>
                    </div>
                    
                    <div class="layer-item-novo" onclick="toggleLayerNovo('ventos')">
                        <div class="layer-item-info">
                            <div class="layer-item-icon" style="background: #00e5ff;">
                                <i class="bi bi-wind"></i>
                            </div>
                            <div class="layer-item-details">
                                <div class="layer-item-name">Estações de Vento</div>
                                <div class="layer-item-count" id="count-ventos-novo">0 estações</div>
                            </div>
                        </div>
                        <div class="layer-item-toggle active" id="toggle-ventos-novo"></div>
                    </div>

                    <div class="layer-item-novo" onclick="toggleLayerNovo('wazeAlertas')">
                        <div class="layer-item-info">
                            <div class="layer-item-icon" style="background: #eab308;">
                                <i class="bi bi-exclamation-circle-fill"></i>
                    </div>
        <div class="layer-item-details">
            <div class="layer-item-name">Alertas Waze</div>
            <div class="layer-item-count" id="count-wazeAlertas-novo">0 alertas</div>
        </div>
    </div>
    <div class="layer-item-toggle active" id="toggle-wazeAlertas-novo"></div>
</div>

<div class="layer-item-novo" onclick="toggleLayerNovo('wazeJams')">
    <div class="layer-item-info">
        <div class="layer-item-icon" style="background: #ff4500;">
            <i class="bi bi-car-front-fill"></i>
        </div>
        <div class="layer-item-details">
            <div class="layer-item-name">Trânsito Waze</div>
            <div class="layer-item-count" id="count-wazeJams-novo">0 jams</div>
        </div>
    </div>
    <div class="layer-item-toggle active" id="toggle-wazeJams-novo"></div>
</div>


                </div>
                
                <div class="layer-group">
                    <div class="layer-group-title">
                        <i class="bi bi-building"></i>
                        Infraestrutura
                    </div>
                    
                    <div class="layer-item-novo" onclick="toggleLayerNovo('escolas')">
                        <div class="layer-item-info">
                            <div class="layer-item-icon" style="background: #ff6b35;">
                                <i class="bi bi-building-fill"></i>
                            </div>
                            <div class="layer-item-details">
                                <div class="layer-item-name">Escolas Municipais</div>
                                <div class="layer-item-count" id="count-escolas-novo">0 escolas</div>
                            </div>
                        </div>
                        <div class="layer-item-toggle active" id="toggle-escolas-novo"></div>
                    </div>
                    
                    <div class="layer-item-novo" onclick="toggleLayerNovo('bensTombados')">
                        <div class="layer-item-info">
                            <div class="layer-item-icon" style="background: #a855f7;">
                                <i class="bi bi-building-fill-check"></i>
                            </div>
                            <div class="layer-item-details">
                                <div class="layer-item-name">Bens Tombados</div>
                                <div class="layer-item-count" id="count-bensTombados-novo">0 locais</div>
                            </div>
                        </div>
                        <div class="layer-item-toggle active" id="toggle-bensTombados-novo"></div>
                    </div>
                </div>
                
                <div class="layer-group">
                    <div class="status-badge status-normalidade" id="status-badge-novo">
                        RIO: NORMALIDADE
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(panel);
}

function togglePanel() {
    const panel = document.getElementById('layer-control-novo');
    const icon = panel.querySelector('.layer-toggle-button i');

    isPanelCollapsed = !isPanelCollapsed;

    if (isPanelCollapsed) {
        panel.classList.add('collapsed');
        icon.className = 'bi bi-chevron-left';
    } else {
        panel.classList.remove('collapsed');
        icon.className = 'bi bi-chevron-right';
    }
}

function toggleLayerNovo(layerName) {
    layerStatesNovo[layerName] = !layerStatesNovo[layerName];
    const toggle = document.getElementById('toggle-' + layerName + '-novo');
    
    if (toggle) {
        toggle.classList.toggle('active');
    }
    
    // ✅ VERIFICAR se mapa e markers existem
    if (typeof map === 'undefined' || !markers) {
        console.warn('⏳ Aguardando mapa/markers serem inicializados...');
        return;
    }
    
    // ✅ VERIFICAR se a camada existe
    if (!markers[layerName]) {
        console.warn(`⚠️ Camada "${layerName}" não encontrada em markers`);
        return;
    }
    
    // Adicionar ou remover camada
    if (layerStatesNovo[layerName]) {
        if (!map.hasLayer(markers[layerName])) {
            map.addLayer(markers[layerName]);
        }
    } else {
        if (map.hasLayer(markers[layerName])) {
            map.removeLayer(markers[layerName]);
        }
    }
    
    // Toggle Waze layers
    if (layerName === 'wazeAlertas' && window.wazeAlertasLayer) {
        if (layerStatesNovo[layerName]) {
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
        if (layerStatesNovo[layerName]) {
            if (!map.hasLayer(window.wazeJamsLayer)) {
                map.addLayer(window.wazeJamsLayer);
            }
        } else {
            if (map.hasLayer(window.wazeJamsLayer)) {
                map.removeLayer(window.wazeJamsLayer);
            }
        }
    }
    
    updateLayerCountsNovo();
}


function updateLayerCountsNovo() {
    if (!markers.sirenes) return;

    const counts = {
        sirenes: markers.sirenes.getLayers().length,
        eventos: markers.eventos.getLayers().length,
        ocorrencias: markers.ocorrencias.getLayers().length,
        pluviometros: markers.pluviometros.getLayers().length,
        ventos: markers.ventos.getLayers().length,
        escolas: markers.escolas.getLayers().length,
        bensTombados: markers.bensTombados.getLayers().length
    };

    document.getElementById('count-sirenes-novo').textContent = counts.sirenes + ' ativos';
    document.getElementById('count-eventos-novo').textContent = counts.eventos + ' programados';
    document.getElementById('count-ocorrencias-novo').textContent = counts.ocorrencias + ' abertas';
    document.getElementById('count-pluviometros-novo').textContent = counts.pluviometros + ' estações';
    document.getElementById('count-ventos-novo').textContent = counts.ventos + ' estações';
    document.getElementById('count-escolas-novo').textContent = counts.escolas + ' escolas';
    document.getElementById('count-bensTombados-novo').textContent = counts.bensTombados + ' locais';

    // Update Waze counts
if (window.wazeAlertasLayer) {
    const alertasCount = window.wazeAlertasLayer.getLayers().length;
    document.getElementById('count-wazeAlertas-novo').textContent = alertasCount + ' alertas';
}

if (window.wazeJamsLayer) {
    const jamsCount = window.wazeJamsLayer.getLayers().length;
    document.getElementById('count-wazeJams-novo').textContent = jamsCount + ' jams';
}
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createLayerControlNovo);
} else {
    createLayerControlNovo();
}

console.log('✅ layer_control_novo.js carregado');

// Conectar botão externo ao toggle
document.addEventListener('DOMContentLoaded', () => {
    const layersBtn = document.getElementById('layers-toggle');
    if (layersBtn) {
        layersBtn.addEventListener('click', togglePanel);
        console.log('✅ Botão de camadas externo conectado');
    }
});