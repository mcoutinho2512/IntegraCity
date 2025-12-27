/**
 * map_init.js - Inicialização do Mapa
 */
let map;
let markers = {};

function initMap() {
    console.log('Iniciando mapa...');

    map = L.map('map', {
        center: [-22.9068, -43.1729],  // ← Centraliza no Rio ao abrir
        zoom: 11,                       // ← Zoom inicial no Rio
        minZoom: 3,                     // ← Permite ver o mundo todo (era 10)
        maxZoom: 18,                    // ← Zoom máximo (mantém)
        zoomControl: true
        // maxBounds REMOVIDO - Agora pode navegar livremente! 🌍
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    console.log('Mapa inicializado');

    // Criar grupos de marcadores
    markers.sirenes = L.layerGroup().addTo(map);
    markers.eventos = L.layerGroup().addTo(map);
    markers.ocorrencias = L.layerGroup().addTo(map);
    markers.pluviometros = L.layerGroup().addTo(map);
    markers.ventos = L.layerGroup().addTo(map);
    markers.bolsoes = L.layerGroup().addTo(map);
    markers.escolas = L.layerGroup().addTo(map);
    markers.bensTombados = L.layerGroup().addTo(map);
    markers.cameras = L.layerGroup().addTo(map);

    carregarDados();
}

async function carregarDados() {
    console.log('Carregando dados das APIs...');

    try {
        await Promise.all([
            carregarSirenes(),
            carregarEventos(),
            carregarOcorrencias(),
            carregarPluviometros(),
            carregarVentos(),
            carregarBolsoes(),
            carregarEscolas(),
            carregarBensTombados(),
            carregarCameras()
        ]);
        console.log('Dados carregados com sucesso');
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
    }
}

async function carregarSirenes() {
    try {
        const response = await fetch('/api/sirenes/');
        const data = await response.json();

        if (!data.success) return;

        markers.sirenes.clearLayers();

        data.data.forEach(sirene => {
            if (sirene.lat && sirene.lng) {
                // Criar ícone personalizado
                const icon = L.divIcon({
                    html: `<div class="marker-sirene ${sirene.prioridade || 'media'}">
                             <i class="bi bi-megaphone-fill"></i>
                           </div>`,
                    className: 'custom-marker',
                    iconSize: [36, 36],
                    iconAnchor: [18, 36]
                });

                // Criar popup
                const popup = `
                    <div class="custom-popup">
                        <div class="popup-header" style="background: ${getCorSirene(sirene.prioridade)}">
                            <span class="popup-icon">🚨</span>
                            <strong>Sirene: ${sirene.nome}</strong>
                        </div>
                        <div class="popup-body">
                            <div class="popup-info">
                                <strong>📍 Endereço:</strong>
                                <p>${sirene.endereco || 'Sem endereço'}</p>
                            </div>
                            <div class="popup-info">
                                <strong>🏘️ Bairro:</strong>
                                <p>${sirene.bairro || 'Sem bairro'}</p>
                            </div>
                            <div class="popup-info">
                                <strong>⚡ Prioridade:</strong>
                                <span class="badge badge-${getNivelPrioridade(sirene.prioridade)}">${sirene.prioridade || 'MÉDIA'}</span>
                            </div>
                            <div class="popup-info">
                                <strong>📊 Status:</strong>
                                <span>${sirene.status || 'inativa'}</span>
                            </div>
                        </div>
                    </div>
                `;

                const marker = L.marker([sirene.lat, sirene.lng], { icon }).bindPopup(popup);
                markers.sirenes.addLayer(marker);
            }
        });

        console.log(data.count + ' sirenes plotadas');
        updateLayerCounts();
    } catch (error) {
        console.error('Erro ao carregar sirenes:', error);
    }
}

// Funções auxiliares
function getCorSirene(prioridade) {
    const cores = {
        'alta': '#ef4444',
        'muito alta': '#dc2626',
        'média': '#f59e0b',
        'media': '#f59e0b',
        'baixa': '#10b981'
    };
    return cores[prioridade?.toLowerCase()] || '#f59e0b';
}

function getNivelPrioridade(prioridade) {
    const nivel = prioridade?.toLowerCase() || 'media';
    if (nivel.includes('alta')) return 'alto';
    if (nivel.includes('baixa')) return 'baixo';
    return 'medio';
}
async function carregarEventos() {
    const response = await fetch('/api/eventos/');
    const data = await response.json();

    markers.eventos.clearLayers();

    data.data.forEach(evento => {
        const icon = createCustomDivIcon('evento', evento.prioridade, 35);

        const marker = L.marker([evento.lat, evento.lng], { icon })
            .bindPopup('<div class="custom-popup"><div class="popup-header" style="background:' + getColorByPriority(evento.prioridade) + '"><h6 class="popup-title">Evento: ' + evento.nome + '</h6></div><div class="popup-body"><p><strong>Tipo:</strong> ' + evento.tipo + '</p><p><strong>Data:</strong> ' + formatData(evento.data) + '</p></div></div>');

        markers.eventos.addLayer(marker);
    });

    console.log(data.count + ' eventos plotados');
    updateLayerCounts();
}

function createOcorrenciaPopup(ocorrencia) {
    // Ícone baseado no nível
    let icone = '⚠️';
    if (ocorrencia.nivel === 'alto') icone = '🚨';
    else if (ocorrencia.nivel === 'medio') icone = '⚠️';
    else icone = 'ℹ️';

    return `
        <div class="custom-popup ocorrencia-popup">
            <div class="popup-header" style="background: ${ocorrencia.cor || '#f59e0b'};">
                <span class="popup-icon">${icone}</span>
                <strong>${ocorrencia.tipo}</strong>
            </div>
            <div class="popup-body">
                <div class="popup-info">
                    <strong>📍 Local:</strong>
                    <p>${ocorrencia.location || ocorrencia.descricao}</p>
                </div>
                <div class="popup-info">
                    <strong>⚡ Prioridade:</strong>
                    <span class="badge badge-${ocorrencia.nivel || 'medio'}">${ocorrencia.prioridade || 'MÉDIA'}</span>
                </div>
                <div class="popup-info">
                    <strong>📊 Nível:</strong>
                    <span class="nivel-badge nivel-${ocorrencia.nivel || 'medio'}">${(ocorrencia.nivel || 'medio').toUpperCase()}</span>
                </div>
                <div class="popup-info">
                    <strong>📋 Status:</strong>
                    <span>${ocorrencia.status || 'Em andamento'}</span>
                </div>
                ${ocorrencia.data_formatada ? `
                <div class="popup-info">
                    <strong>🕐 Data:</strong>
                    <p>${ocorrencia.data_formatada}</p>
                </div>
                ` : ''}
            </div>
        </div>
    `;
}

function createOcorrenciaIcon(ocorrencia) {
    let cor = '#f59e0b'; // Amarelo padrão

    if (ocorrencia.nivel === 'alto' || ocorrencia.prioridade === 'ALTA' || ocorrencia.prioridade === 'MUITO ALTA') {
        cor = '#ef4444'; // Vermelho
    } else if (ocorrencia.nivel === 'medio' || ocorrencia.prioridade === 'MÉDIA') {
        cor = '#f59e0b'; // Amarelo
    } else {
        cor = '#10b981'; // Verde
    }

    return L.divIcon({
        html: `<div style="background: ${cor};" class="marker-ocorrencia"><i class="bi bi-exclamation-triangle-fill"></i></div>`,
        className: 'custom-marker',
        iconSize: [32, 32]
    });
}

async function carregarPluviometros() {
    try {
        const response = await fetch('/api/pluviometros/');
        const data = await response.json();

        if (!data.success) return;

        markers.pluviometros.clearLayers();

        data.data.forEach(plv => {
            if (plv.lat && plv.lng) {
                const icon = L.divIcon({
                    className: 'custom-marker',
                    html: `<div class="marker-icon marker-pluviometro">
                             <i class="bi bi-cloud-drizzle-fill"></i>
                             <span class="rain-indicator">${plv.chuva_1h}mm</span>
                           </div>`,
                    iconSize: [40, 40],
                    iconAnchor: [20, 40]
                });

                const popup = '<div class="custom-popup"><div class="popup-header" style="background:#3b82f6"><h6 class="popup-title"><i class="bi bi-cloud-rain"></i> ' + plv.nome + '</h6></div><div class="popup-body"><p><strong>Chuva 1h:</strong> ' + plv.chuva_1h + ' mm</p><p><strong>Chuva 4h:</strong> ' + plv.chuva_4h + ' mm</p><p><strong>Chuva 24h:</strong> ' + plv.chuva_24h + ' mm</p><p><strong>Chuva 96h:</strong> ' + plv.chuva_96h + ' mm</p><div class="popup-timestamp">Atualizado: ' + plv.data + '</div></div></div>';

                const marker = L.marker([plv.lat, plv.lng], { icon }).bindPopup(popup);
                markers.pluviometros.addLayer(marker);
            }
        });

        console.log(data.count + ' pluviometros plotados');
        updateLayerCounts();
    } catch (error) {
        console.error('Erro ao carregar pluviometros:', error);
    }
}

async function carregarVentos() {
    try {
        const response = await fetch('/api/ventos/');
        const data = await response.json();

        if (!data.success) return;

        markers.ventos.clearLayers();

        data.data.forEach(vento => {
            if (vento.lat && vento.lng) {
                const icon = L.divIcon({
                    className: 'custom-marker',
                    html: `<div class="marker-icon marker-vento">
                             <i class="bi bi-wind"></i>
                             <span class="wind-speed">${vento.velocidade.toFixed(1)}</span>
                           </div>`,
                    iconSize: [40, 40],
                    iconAnchor: [20, 40]
                });

                const popup = `<div class="custom-popup">
                    <div class="popup-header" style="background:#00e5ff">
                        <h6 class="popup-title"><i class="bi bi-wind"></i> ${vento.nome}</h6>
                    </div>
                    <div class="popup-body">
                        <p><strong>🌡️ Temperatura:</strong> ${vento.temperatura}°C</p>
                        <p><strong>💧 Umidade:</strong> ${vento.umidade}%</p>
                        <p><strong>🌬️ Velocidade:</strong> ${vento.velocidade} m/s</p>
                        <p><strong>🧭 Direção:</strong> ${vento.direcao}</p>
                        <div class="popup-timestamp">Atualizado: ${vento.data}</div>
                    </div>
                </div>`;

                const marker = L.marker([vento.lat, vento.lng], { icon }).bindPopup(popup);
                markers.ventos.addLayer(marker);
            }
        });

        console.log(data.count + ' estações de vento plotadas');
        updateLayerCounts();
    } catch (error) {
        console.error('Erro ao carregar ventos:', error);
    }
}

async function carregarOcorrencias() {
    try {
        const response = await fetch('/api/ocorrencias/tempo-real/');
        const data = await response.json();

        if (!data.success) return;

        markers.ocorrencias.clearLayers();

        data.data.forEach(ocorrencia => {
            if (ocorrencia.lat && ocorrencia.lng) {
                const marker = L.marker([ocorrencia.lat, ocorrencia.lng], {
                    icon: createOcorrenciaIcon(ocorrencia)
                });

                marker.bindPopup(createOcorrenciaPopup(ocorrencia));
                markers.ocorrencias.addLayer(marker);
            }
        });

        console.log(data.count + ' ocorrencias plotadas');
        updateLayerCounts();
    } catch (error) {
        console.error('Erro ao carregar ocorrências:', error);
    }
}

async function carregarBolsoes() {
    try {
        const response = await fetch('/api/tixxi/bolsoes/');
        const data = await response.json();

        console.log('Resposta bolsões:', data);

        if (!data.success || !data.data) return;

        markers.bolsoes.clearLayers();

        data.data.forEach(bolsao => {
            if (bolsao.lat && bolsao.lng) {
                const icon = L.divIcon({
                    className: 'custom-marker',
                    html: '<div class="marker-icon marker-bolsao"><i class="bi bi-water"></i></div>',
                    iconSize: [35, 35],
                    iconAnchor: [17, 35]
                });

                const popup = `<div class="custom-popup">
                    <div class="popup-header" style="background:#06b6d4">
                        <h6 class="popup-title"><i class="bi bi-water"></i> Bolsão de Alagamento</h6>
                    </div>
                    <div class="popup-body">
                        <p><strong>📍 Local:</strong> ${bolsao.local}</p>
                        <p><strong>🔍 Referência:</strong> ${bolsao.referencia}</p>
                        <p><strong>🏘️ Bairro:</strong> ${bolsao.bairro}</p>
                        <p><strong>🗺️ Zona:</strong> ${bolsao.zona}</p>
                    </div>
                </div>`;

                const marker = L.marker([bolsao.lat, bolsao.lng], { icon }).bindPopup(popup);
                markers.bolsoes.addLayer(marker);
            }
        });

        console.log(data.count + ' bolsões plotados');
        updateLayerCounts();
    } catch (error) {
        console.error('Erro ao carregar bolsões:', error);
    }
}

async function carregarEscolas() {
    try {
        const response = await fetch('/api/tixxi/escolas/');
        const data = await response.json();

        console.log('Resposta escolas TIXXI:', data);

        if (!data.success || !data.data) return;

        markers.escolas.clearLayers();

        data.data.forEach(escola => {
            if (escola.lat && escola.lng) {
                const icon = L.divIcon({
                    className: 'custom-marker',
                    html: '<div class="marker-icon marker-escola"><i class="bi bi-building"></i></div>',
                    iconSize: [35, 35],
                    iconAnchor: [17, 35]
                });

                const popup = `<div class="custom-popup">
                    <div class="popup-header" style="background:#ff6b35">
                        <h6 class="popup-title"><i class="bi bi-building"></i> ${escola.nome}</h6>
                    </div>
                    <div class="popup-body">
                        <p><strong>📍 Endereço:</strong> ${escola.endereco || 'N/A'}</p>
                        <p><strong>🏘️ Bairro:</strong> ${escola.bairro || 'N/A'}</p>
                        <p><strong>📞 Telefone:</strong> ${escola.telefone || 'N/A'}</p>
                        <p><strong>🏫 Tipo:</strong> ${escola.tipo || 'Escola Municipal'}</p>
                    </div>
                </div>`;

                const marker = L.marker([escola.lat, escola.lng], { icon }).bindPopup(popup);
                markers.escolas.addLayer(marker);
            }
        });

        console.log(data.count + ' escolas TIXXI plotadas');
        updateLayerCounts();
    } catch (error) {
        console.error('Erro ao carregar escolas:', error);
    }
}

async function carregarBensTombados() {
    try {
        const response = await fetch('/api/bens-tombados/');
        const data = await response.json();

        console.log('Resposta bens tombados:', data);

        if (!data.success || !data.data) return;

        markers.bensTombados.clearLayers();

        data.data.forEach(bem => {
            if (bem.lat && bem.lng) {
                const icon = L.divIcon({
                    className: 'custom-marker',
                    html: '<div class="marker-icon marker-bem-tombado"><i class="bi bi-building-fill-check"></i></div>',
                    iconSize: [35, 35],
                    iconAnchor: [17, 35]
                });

                const popup = `<div class="custom-popup">
                    <div class="popup-header" style="background:#8b5cf6">
                        <h6 class="popup-title"><i class="bi bi-building-fill-check"></i> ${bem.nome}</h6>
                    </div>
                    <div class="popup-body">
                        <p><strong>📍 Localização:</strong> ${bem.rua}</p>
                        <p><strong>⭐ Grau de Proteção:</strong> ${bem.grau}</p>
                    </div>
                </div>`;

                const marker = L.marker([bem.lat, bem.lng], { icon }).bindPopup(popup);
                markers.bensTombados.addLayer(marker);
            }
        });

        console.log(data.count + ' bens tombados plotados');
        updateLayerCounts();
    } catch (error) {
        console.error('Erro ao carregar bens tombados:', error);
    }
}

async function carregarCameras() {
    try {
        const response = await fetch('/api/tixxi/cameras/');
        const data = await response.json();

        console.log('Resposta câmeras TIXXI:', data);

        if (!data.success || !data.data) return;

        markers.cameras.clearLayers();

        data.data.forEach(camera => {
            if (camera.lat && camera.lng) {
                const icon = L.divIcon({
                    className: 'custom-marker',
                    html: '<div class="marker-icon marker-camera"><i class="bi bi-camera-video-fill"></i></div>',
                    iconSize: [30, 30],
                    iconAnchor: [15, 30]
                });

                const popup = `<div class="custom-popup">
                    <div class="popup-header" style="background:#10b981">
                        <h6 class="popup-title"><i class="bi bi-camera-video-fill"></i> ${camera.nome || 'Câmera'}</h6>
                    </div>
                    <div class="popup-body">
                        <p><strong>📍 Local:</strong> ${camera.endereco || camera.local || 'N/A'}</p>
                        <p><strong>🏘️ Bairro:</strong> ${camera.bairro || 'N/A'}</p>
                        <p><strong>📊 Status:</strong> ${camera.status || 'Ativa'}</p>
                    </div>
                </div>`;

                const marker = L.marker([camera.lat, camera.lng], { icon }).bindPopup(popup);
                markers.cameras.addLayer(marker);
            }
        });

        console.log(data.count + ' câmeras TIXXI plotadas');
        updateLayerCounts();
    } catch (error) {
        console.error('Erro ao carregar câmeras:', error);
    }
}

// ===== ATUALIZAÇÃO AUTOMÁTICA DE OCORRÊNCIAS =====
setInterval(() => {
    console.log('🔄 Atualizando ocorrências...');

    fetch('/api/ocorrencias/tempo-real/')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Limpar marcadores antigos
                markers.ocorrencias.clearLayers();

                // Adicionar novos
                data.data.forEach(ocorrencia => {
                    if (ocorrencia.lat && ocorrencia.lng) {
                        const marker = L.marker([ocorrencia.lat, ocorrencia.lng], {
                            icon: createOcorrenciaIcon(ocorrencia)
                        });

                        marker.bindPopup(createOcorrenciaPopup(ocorrencia));
                        markers.ocorrencias.addLayer(marker);
                    }
                });

                console.log(`✅ ${data.count} ocorrências atualizadas`);
                updateLayerCountsNovo();
            }
        })
        .catch(err => console.error('Erro ao atualizar ocorrências:', err));
}, 30000); // 30 segundos


function updateLayerCounts() {
    // Atualizar painel novo se existir
    if (typeof updateLayerCountsNovo === 'function') {
        updateLayerCountsNovo();
    }
}

setInterval(carregarDados, 30000);

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMap);
} else {
    initMap();
}

console.log('map_init.js carregado');