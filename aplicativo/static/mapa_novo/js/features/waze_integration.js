/**
 * waze_integration.js - Integracao com dados do Waze
 */

class WazeIntegration {
    constructor(map) {
        this.map = map;
        this.alertasLayer = L.layerGroup();
        this.jamsLayer = L.layerGroup();
        this.alertasClusterLayer = L.layerGroup();
        this.jamsHeatLayer = L.layerGroup();

        this.alertTypeConfig = {
            ACCIDENT: { label: 'Acidentes', color: '#ef4444' },
            HAZARD: { label: 'Perigos', color: '#f59e0b' },
            ROAD_CLOSED: { label: 'Vias fechadas', color: '#8b5cf6' },
            JAM: { label: 'Jams (alertas)', color: '#f97316' },
            OTHER: { label: 'Outros', color: '#64748b' }
        };

        this.filters = {
            sinceMinutes: 60,
            types: {
                ACCIDENT: true,
                HAZARD: true,
                ROAD_CLOSED: true,
                JAM: true,
                OTHER: true
            },
            severity: {
                alta: true,
                media: true,
                baixa: true
            },
            heatmap: true,
            showCritical: true
        };

        this.priorityRoutes = Array.isArray(window.wazePriorityRoutes)
            ? window.wazePriorityRoutes.map(r => String(r).toLowerCase())
            : [];

        this.dataCache = {
            alertas: [],
            jams: []
        };

        this.init();
    }

    init() {
        console.log('Iniciando integracao Waze...');

        this.alertasLayer.addTo(this.map);
        this.jamsLayer.addTo(this.map);

        window.wazeAlertasLayer = this.alertasLayer;
        window.wazeJamsLayer = this.jamsLayer;

        if (typeof markers !== 'undefined') {
            markers.wazeAlertas = this.alertasLayer;
            markers.wazeJams = this.jamsLayer;
        }

        this.ensureUi();
        this.bindUi();

        this.loadWazeData();
        setInterval(() => this.loadWazeData(), 300000);

        this.map.on('zoomend', () => this.refreshClusterVisibility());
    }

    ensureUi() {
        if (!document.getElementById('waze-legend')) {
            const legend = document.createElement('div');
            legend.id = 'waze-legend';
            legend.className = 'waze-legend';
            legend.innerHTML = this.renderLegend();
            document.body.appendChild(legend);
        }

        if (!document.getElementById('waze-panel')) {
            const panel = document.createElement('div');
            panel.id = 'waze-panel';
            panel.className = 'waze-panel';
            panel.innerHTML = this.renderPanel();
            document.body.appendChild(panel);
        }

        if (!document.getElementById('waze-sidebar')) {
            const sidebar = document.createElement('div');
            sidebar.id = 'waze-sidebar';
            sidebar.className = 'waze-sidebar';
            sidebar.innerHTML = '<div class="waze-sidebar-header">Waze - Ocorrencias</div><div class="waze-sidebar-body" id="waze-sidebar-body">Sem dados</div>';
            document.body.appendChild(sidebar);
        }
    }

    renderLegend() {
        return `
            <div class="waze-legend-title">Waze - Legenda</div>
            <div class="waze-legend-section">
                <div class="waze-legend-item"><span class="dot" style="background:#ef4444"></span>Acidente</div>
                <div class="waze-legend-item"><span class="dot" style="background:#f59e0b"></span>Perigo</div>
                <div class="waze-legend-item"><span class="dot" style="background:#8b5cf6"></span>Via fechada</div>
            </div>
            <div class="waze-legend-section">
                <div class="waze-legend-item"><span class="line" style="background:#22c55e"></span>Jam nivel 1</div>
                <div class="waze-legend-item"><span class="line" style="background:#f59e0b"></span>Jam nivel 2</div>
                <div class="waze-legend-item"><span class="line" style="background:#f97316"></span>Jam nivel 3</div>
                <div class="waze-legend-item"><span class="line" style="background:#ef4444"></span>Jam nivel 4</div>
                <div class="waze-legend-item"><span class="line" style="background:#b91c1c"></span>Jam nivel 5</div>
            </div>
        `;
    }

    renderPanel() {
        return `
            <div class="waze-panel-header">Waze - Controles</div>
            <div class="waze-panel-body">
                <label class="waze-panel-label">Janela de tempo</label>
                <select id="waze-filter-time" class="waze-panel-select">
                    <option value="15">Ultimos 15 min</option>
                    <option value="30">Ultimos 30 min</option>
                    <option value="60" selected>Ultimos 60 min</option>
                    <option value="120">Ultimos 120 min</option>
                </select>

                <label class="waze-panel-label">Tipos de alertas</label>
                <div class="waze-panel-group">
                    ${Object.keys(this.alertTypeConfig).map(key => `
                        <label class="waze-panel-check">
                            <input type="checkbox" data-waze-type="${key}" checked>
                            <span>${this.alertTypeConfig[key].label}</span>
                        </label>
                    `).join('')}
                </div>

                <label class="waze-panel-label">Severidade</label>
                <div class="waze-panel-group">
                    <label class="waze-panel-check"><input type="checkbox" data-waze-sev="alta" checked><span>Alta</span></label>
                    <label class="waze-panel-check"><input type="checkbox" data-waze-sev="media" checked><span>Media</span></label>
                    <label class="waze-panel-check"><input type="checkbox" data-waze-sev="baixa" checked><span>Baixa</span></label>
                </div>

                <label class="waze-panel-label">Camadas</label>
                <div class="waze-panel-group">
                    <label class="waze-panel-check"><input type="checkbox" id="waze-toggle-heat" checked><span>Heatmap jams</span></label>
                    <label class="waze-panel-check"><input type="checkbox" id="waze-toggle-critical" checked><span>Destaque criticos</span></label>
                </div>
            </div>
        `;
    }

    bindUi() {
        const timeSelect = document.getElementById('waze-filter-time');
        if (timeSelect) {
            timeSelect.addEventListener('change', (event) => {
                const value = parseInt(event.target.value, 10);
                this.filters.sinceMinutes = Number.isNaN(value) ? 60 : value;
                this.loadWazeData();
            });
        }

        document.querySelectorAll('[data-waze-type]').forEach(input => {
            input.addEventListener('change', () => {
                const type = input.getAttribute('data-waze-type');
                this.filters.types[type] = input.checked;
                this.renderData();
            });
        });

        document.querySelectorAll('[data-waze-sev]').forEach(input => {
            input.addEventListener('change', () => {
                const sev = input.getAttribute('data-waze-sev');
                this.filters.severity[sev] = input.checked;
                this.renderData();
            });
        });

        const heatToggle = document.getElementById('waze-toggle-heat');
        if (heatToggle) {
            heatToggle.addEventListener('change', () => {
                this.filters.heatmap = heatToggle.checked;
                this.renderHeatmap();
            });
        }

        const criticalToggle = document.getElementById('waze-toggle-critical');
        if (criticalToggle) {
            criticalToggle.addEventListener('change', () => {
                this.filters.showCritical = criticalToggle.checked;
                this.renderData();
            });
        }
    }

    async loadWazeData() {
        try {
            const params = new URLSearchParams({
                since_minutes: String(this.filters.sinceMinutes)
            });
            const response = await fetch(`/api/waze/?${params.toString()}`);
            const data = await response.json();

            if (data.success) {
                this.dataCache.alertas = data.alertas || [];
                this.dataCache.jams = data.congestionamentos || [];
                this.renderData();
            } else {
                console.warn('Waze API retornou sem sucesso:', data.error);
            }
        } catch (error) {
            console.error('Erro ao carregar dados Waze:', error);
        }
    }

    renderData() {
        this.renderAlertas();
        this.renderJams();
        this.renderSidebar();
        this.renderHeatmap();
        this.refreshClusterVisibility();

        if (typeof updateLayerCountsNovo === 'function') {
            updateLayerCountsNovo();
        }
    }

    renderAlertas() {
        this.alertasLayer.clearLayers();
        this.alertasClusterLayer.clearLayers();

        const alertas = this.getFilteredAlertas();
        const clusters = this.groupAlertsForCluster(alertas);

        alertas.forEach(alerta => {
            if (!alerta.lat || !alerta.lng) return;

            const color = this.alertTypeColor(alerta.tipo_raw);
            const icon = L.divIcon({
                html: `<div class="waze-alert-dot" style="background:${color}"></div>`,
                className: 'waze-alert-marker',
                iconSize: [18, 18]
            });

            const marker = L.marker([alerta.lat, alerta.lng], { icon });

            const popup = `
                <div class="custom-popup">
                    <div class="popup-header" style="background:${color}">
                        <h6 class="popup-title">Waze: ${alerta.tipo || 'Alerta'}</h6>
                    </div>
                    <div class="popup-body">
                        ${alerta.subtipo ? `<p><strong>Tipo:</strong> ${alerta.subtipo}</p>` : ''}
                        <p><strong>Local:</strong> ${alerta.rua || 'N/A'}</p>
                        <p><strong>Cidade:</strong> ${alerta.cidade || 'N/A'}</p>
                        <p><strong>Confianca:</strong> ${alerta.confianca || 0}/10</p>
                        <p><strong>Severidade:</strong> ${alerta.severidade || 'baixa'}</p>
                    </div>
                </div>
            `;

            marker.bindPopup(popup);
            marker.bindTooltip(alerta.rua || 'Via nao identificada');
            marker.addTo(this.alertasLayer);
        });

        clusters.forEach(cluster => {
            const icon = L.divIcon({
                html: `<div class="waze-cluster">${cluster.count}</div>`,
                className: 'waze-cluster-marker',
                iconSize: [34, 34]
            });
            const marker = L.marker([cluster.lat, cluster.lng], { icon });
            marker.bindTooltip(`${cluster.count} alertas`);
            marker.on('click', () => {
                this.map.setView([cluster.lat, cluster.lng], this.map.getZoom() + 2);
            });
            marker.addTo(this.alertasClusterLayer);
        });

        if (this.shouldCluster()) {
            if (this.map.hasLayer(this.alertasLayer)) {
                this.map.removeLayer(this.alertasLayer);
            }
            if (!this.map.hasLayer(this.alertasClusterLayer)) {
                this.map.addLayer(this.alertasClusterLayer);
            }
        } else {
            if (this.map.hasLayer(this.alertasClusterLayer)) {
                this.map.removeLayer(this.alertasClusterLayer);
            }
            if (!this.map.hasLayer(this.alertasLayer)) {
                this.map.addLayer(this.alertasLayer);
            }
        }
    }

    renderJams() {
        this.jamsLayer.clearLayers();
        const jams = this.getFilteredJams();

        jams.forEach(jam => {
            if (!jam.linha || jam.linha.length === 0) return;

            const points = jam.linha.map(p => [p.y, p.x]);
            const color = this.jamLevelColor(jam.nivel);
            const isPriority = this.isPriorityRoute(jam.rua);
            const weight = jam.critico && this.filters.showCritical ? 8 : 5;

            const polyline = L.polyline(points, {
                color,
                weight,
                opacity: isPriority ? 0.95 : 0.8,
                dashArray: isPriority ? '6 6' : null
            });

            const popup = `
                <div class="custom-popup">
                    <div class="popup-header" style="background:${color}">
                        <h6 class="popup-title">${jam.nivel_texto || 'Congestionamento'}</h6>
                    </div>
                    <div class="popup-body">
                        <p><strong>Local:</strong> ${jam.rua || 'N/A'}</p>
                        <p><strong>Cidade:</strong> ${jam.cidade || 'N/A'}</p>
                        <p><strong>Velocidade:</strong> ${jam.velocidade || 0} km/h</p>
                        <p><strong>Comprimento:</strong> ${jam.comprimento || 0} m</p>
                        <p><strong>Atraso:</strong> ${jam.atraso_min || 0} min</p>
                    </div>
                </div>
            `;

            polyline.bindPopup(popup);
            polyline.bindTooltip(jam.rua || 'Via nao identificada');
            polyline.addTo(this.jamsLayer);
        });
    }

    renderHeatmap() {
        this.jamsHeatLayer.clearLayers();
        if (!this.filters.heatmap) {
            if (this.map.hasLayer(this.jamsHeatLayer)) {
                this.map.removeLayer(this.jamsHeatLayer);
            }
            return;
        }

        const jams = this.getFilteredJams();
        jams.forEach(jam => {
            if (!jam.lat || !jam.lng) return;

            const radius = Math.max(80, Math.min(300, (jam.comprimento || 0) / 2));
            const color = this.jamLevelColor(jam.nivel);
            const circle = L.circle([jam.lat, jam.lng], {
                radius,
                color,
                fillColor: color,
                fillOpacity: 0.25,
                weight: 1
            });

            circle.addTo(this.jamsHeatLayer);
        });

        if (!this.map.hasLayer(this.jamsHeatLayer)) {
            this.map.addLayer(this.jamsHeatLayer);
        }
    }

    renderSidebar() {
        const container = document.getElementById('waze-sidebar-body');
        if (!container) return;

        const items = [];
        this.getFilteredAlertas().forEach(alerta => {
            items.push({
                kind: 'alert',
                score: this.alertScore(alerta),
                title: `${alerta.tipo || 'Alerta'} - ${alerta.subtipo || 'Geral'}`,
                rua: alerta.rua || 'Via nao identificada',
                cidade: alerta.cidade || 'N/A',
                lat: alerta.lat,
                lng: alerta.lng,
                meta: `Conf: ${alerta.confianca || 0}/10 | Sev: ${alerta.severidade || 'baixa'}`
            });
        });

        this.getFilteredJams().forEach(jam => {
            items.push({
                kind: 'jam',
                score: this.jamScore(jam),
                title: jam.nivel_texto || 'Congestionamento',
                rua: jam.rua || 'Via nao identificada',
                cidade: jam.cidade || 'N/A',
                lat: jam.lat,
                lng: jam.lng,
                meta: `Delay: ${jam.atraso_min || 0} min | ${jam.comprimento || 0} m`
            });
        });

        items.sort((a, b) => b.score - a.score);
        const top = items.slice(0, 12);

        if (top.length === 0) {
            container.innerHTML = 'Sem dados';
            return;
        }

        container.innerHTML = top.map(item => {
            return `
                <div class="waze-sidebar-item" data-lat="${item.lat}" data-lng="${item.lng}">
                    <div class="waze-sidebar-title">${item.title}</div>
                    <div class="waze-sidebar-sub">${item.rua} - ${item.cidade}</div>
                    <div class="waze-sidebar-meta">${item.meta}</div>
                </div>
            `;
        }).join('');

        container.querySelectorAll('.waze-sidebar-item').forEach(el => {
            el.addEventListener('click', () => {
                const lat = parseFloat(el.getAttribute('data-lat'));
                const lng = parseFloat(el.getAttribute('data-lng'));
                if (!Number.isNaN(lat) && !Number.isNaN(lng)) {
                    this.map.setView([lat, lng], Math.max(this.map.getZoom(), 15));
                }
            });
        });
    }

    getFilteredAlertas() {
        return this.dataCache.alertas.filter(alerta => {
            const typeKey = this.normalizeAlertType(alerta.tipo_raw);
            const sev = alerta.severidade || 'baixa';
            return this.filters.types[typeKey] && this.filters.severity[sev];
        });
    }

    getFilteredJams() {
        return this.dataCache.jams;
    }

    alertTypeColor(typeRaw) {
        const key = this.normalizeAlertType(typeRaw);
        return this.alertTypeConfig[key]?.color || '#64748b';
    }

    normalizeAlertType(typeRaw) {
        if (!typeRaw) return 'OTHER';
        if (this.alertTypeConfig[typeRaw]) return typeRaw;
        return 'OTHER';
    }

    jamLevelColor(level) {
        const colors = {
            0: '#22c55e',
            1: '#84cc16',
            2: '#f59e0b',
            3: '#f97316',
            4: '#ef4444',
            5: '#b91c1c'
        };

        return colors[level] || '#64748b';
    }

    groupAlertsForCluster(alertas) {
        const zoom = this.map.getZoom();
        const cellSize = zoom >= 14 ? 0.002 : zoom >= 12 ? 0.004 : 0.008;
        const grid = new Map();

        alertas.forEach(alerta => {
            if (!alerta.lat || !alerta.lng) return;
            const keyLat = Math.round(alerta.lat / cellSize) * cellSize;
            const keyLng = Math.round(alerta.lng / cellSize) * cellSize;
            const key = `${keyLat.toFixed(3)}:${keyLng.toFixed(3)}`;
            if (!grid.has(key)) {
                grid.set(key, { lat: keyLat, lng: keyLng, count: 0 });
            }
            grid.get(key).count += 1;
        });

        return Array.from(grid.values());
    }

    refreshClusterVisibility() {
        if (this.shouldCluster()) {
            if (this.map.hasLayer(this.alertasLayer)) {
                this.map.removeLayer(this.alertasLayer);
            }
            if (!this.map.hasLayer(this.alertasClusterLayer)) {
                this.map.addLayer(this.alertasClusterLayer);
            }
        } else {
            if (this.map.hasLayer(this.alertasClusterLayer)) {
                this.map.removeLayer(this.alertasClusterLayer);
            }
            if (!this.map.hasLayer(this.alertasLayer)) {
                this.map.addLayer(this.alertasLayer);
            }
        }
    }

    shouldCluster() {
        return this.map.getZoom() < 13;
    }

    alertScore(alerta) {
        const sev = alerta.severidade || 'baixa';
        const sevScore = sev === 'alta' ? 3 : sev === 'media' ? 2 : 1;
        const confidence = alerta.confianca || 0;
        return sevScore * 10 + confidence;
    }

    jamScore(jam) {
        const levelScore = (jam.nivel || 0) * 10;
        const delayScore = jam.atraso_min || 0;
        const lengthScore = Math.min(10, Math.round((jam.comprimento || 0) / 100));
        return levelScore + delayScore + lengthScore;
    }

    isPriorityRoute(roadName) {
        if (!roadName || this.priorityRoutes.length === 0) return false;
        const normalized = String(roadName).toLowerCase();
        return this.priorityRoutes.some(route => normalized.includes(route));
    }
}

function initWaze() {
    if (typeof map !== 'undefined' && map) {
        window.wazeIntegration = new WazeIntegration(map);
    } else {
        setTimeout(initWaze, 500);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWaze);
} else {
    initWaze();
}
