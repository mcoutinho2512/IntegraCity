/**
 * waze_integration.js - Integração com dados do Waze
 */

class WazeIntegration {
    constructor(map) {
        this.map = map;
        this.alertasLayer = L.layerGroup();
        this.jamsLayer = L.layerGroup();

        // ✅ EXPOR GLOBALMENTE para layer_control_novo.js
        window.wazeAlertasLayer = this.alertasLayer;
        window.wazeJamsLayer = this.jamsLayer;

        this.init();
    }

    init() {
        console.log('🚗 Iniciando integração Waze...');

        // Adicionar camadas ao mapa
        this.alertasLayer.addTo(this.map);
        this.jamsLayer.addTo(this.map);

        // ✅ ADICIONAR ao objeto markers global
        if (typeof markers !== 'undefined') {
            markers.wazeAlertas = this.alertasLayer;
            markers.wazeJams = this.jamsLayer;
            console.log('✅ Camadas Waze adicionadas ao objeto markers');
        }

        // Carregar dados
        this.loadWazeData();

        // Atualizar a cada 5 minutos
        setInterval(() => this.loadWazeData(), 300000);
    }

    async loadWazeData() {
        try {
            console.log('📡 Carregando dados do Waze...');
            const response = await fetch('/api/waze/');
            const data = await response.json();

            if (data.success) {
                this.plotAlertas(data.alertas || []);
                this.plotJams(data.congestionamentos || []);

                console.log(`✅ Waze: ${data.alertas?.length || 0} alertas, ${data.congestionamentos?.length || 0} congestionamentos`);
            } else {
                console.warn('⚠️ Waze API retornou sem sucesso:', data.error);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar dados Waze:', error);
        }
    }

    plotAlertas(alertas) {
        // Limpar alertas antigos
        this.alertasLayer.clearLayers();

        alertas.forEach(alerta => {
            if (!alerta.lat || !alerta.lng) return;

            // Ícone por tipo
            const iconHTML = this.getAlertIcon(alerta.tipo, alerta.subtipo);

            const icon = L.divIcon({
                html: iconHTML,
                className: 'waze-alert-marker',
                iconSize: [30, 30]
            });

            const marker = L.marker([alerta.lat, alerta.lng], { icon });

            // Popup
            const popup = `
                <div class="custom-popup">
                    <div class="popup-header" style="background:#00aff5">
                        <h6 class="popup-title">🚨 Waze: ${alerta.tipo}</h6>
                    </div>
                    <div class="popup-body">
                        ${alerta.subtipo ? `<p><strong>Tipo:</strong> ${alerta.subtipo}</p>` : ''}
                        <p><strong>📍 Local:</strong> ${alerta.rua || 'N/A'}</p>
                        <p><strong>🏙️ Cidade:</strong> ${alerta.cidade || 'Rio de Janeiro'}</p>
                        <p><strong>⭐ Confiança:</strong> ${alerta.confianca || 0}/10</p>
                        <div class="popup-timestamp" style="color:#00aff5">Via Waze</div>
                    </div>
                </div>
            `;

            marker.bindPopup(popup);
            marker.addTo(this.alertasLayer);
        });

        console.log(`✅ ${alertas.length} alertas Waze plotados`);
    }

    plotJams(jams) {
        // Limpar congestionamentos antigos
        this.jamsLayer.clearLayers();

        jams.forEach(jam => {
            if (!jam.linha || jam.linha.length === 0) return;

            // Converter pontos para formato Leaflet
            const points = jam.linha.map(p => [p.y, p.x]);

            // Cor por nível de congestionamento
            const colors = {
                0: '#00ff00', // Livre
                1: '#ffff00', // Leve
                2: '#ffa500', // Moderado
                3: '#ff4500', // Pesado
                4: '#ff0000', // Parado
                5: '#8b0000'  // Muito lento
            };

            const color = colors[jam.nivel] || '#808080';

            // Desenhar linha
            const polyline = L.polyline(points, {
                color: color,
                weight: 6,
                opacity: 0.7
            });

            // Popup
            const popup = `
                <div class="custom-popup">
                    <div class="popup-header" style="background:${color}">
                        <h6 class="popup-title">🚗 ${jam.nivel_texto || 'Congestionamento'}</h6>
                    </div>
                    <div class="popup-body">
                        <p><strong>📍 Local:</strong> ${jam.rua || 'N/A'}</p>
                        <p><strong>🏙️ Cidade:</strong> ${jam.cidade || 'Rio de Janeiro'}</p>
                        <p><strong>🚦 Velocidade:</strong> ${jam.velocidade || 0} km/h</p>
                        <p><strong>📏 Comprimento:</strong> ${jam.comprimento || 0}m</p>
                        <p><strong>⏱️ Atraso:</strong> ${Math.round((jam.atraso || 0) / 60)}min</p>
                        <div class="popup-timestamp" style="color:${color}">Via Waze</div>
                    </div>
                </div>
            `;

            polyline.bindPopup(popup);
            polyline.addTo(this.jamsLayer);
        });

        console.log(`✅ ${jams.length} congestionamentos Waze plotados`);
    }

    getAlertIcon(tipo, subtipo) {
        const icons = {
            'Acidente': '💥',
            'Perigo': '⚠️',
            'Buraco': '🔺',  // ← OU '🚧' OU ''
            'Obra': '🚧',
            'Via Fechada': '🚫',
            'Objeto na Pista': '📦',
            'Veículo Parado': '🚙',
            'Semáforo com Defeito': '🚦'
        };

        const emoji = icons[subtipo] || icons[tipo] || '⚠️';

        return `<div style="font-size: 28px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">${emoji}</div>`;
    }

    toggleAlertas(show) {
        if (show) {
            if (!this.map.hasLayer(this.alertasLayer)) {
                this.map.addLayer(this.alertasLayer);
            }
        } else {
            if (this.map.hasLayer(this.alertasLayer)) {
                this.map.removeLayer(this.alertasLayer);
            }
        }
    }

    toggleJams(show) {
        if (show) {
            if (!this.map.hasLayer(this.jamsLayer)) {
                this.map.addLayer(this.jamsLayer);
            }
        } else {
            if (this.map.hasLayer(this.jamsLayer)) {
                this.map.removeLayer(this.jamsLayer);
            }
        }
    }
}

// ✅ Aguardar mapa estar pronto
function initWaze() {
    if (typeof map !== 'undefined' && map) {
        window.wazeIntegration = new WazeIntegration(map);
        console.log('✅ Integração Waze carregada');
    } else {
        console.log('⏳ Aguardando mapa...');
        setTimeout(initWaze, 500);
    }
}

// Inicializar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWaze);
} else {
    initWaze();
}