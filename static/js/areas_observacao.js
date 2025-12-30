/**
 * Sistema de Áreas de Observação - IntegraCity
 * Permite desenhar polígonos e retângulos no mapa para monitoramento
 */

class AreasObservacao {
    constructor(map) {
        console.log('AreasObservacao constructor iniciado');
        this.map = map;
        this.drawnItems = new L.FeatureGroup();
        this.areasLayer = new L.FeatureGroup();
        this.drawControl = null;
        this.areasSalvas = [];
        this.areaAtual = null;

        // Detectar base URL do site
        this.baseUrl = this.detectBaseUrl();

        this.map.addLayer(this.drawnItems);
        this.map.addLayer(this.areasLayer);
        console.log('Layers adicionadas ao mapa');

        this.initDrawControl();
        console.log('DrawControl inicializado:', this.drawControl);

        this.initEventHandlers();
        console.log('Event handlers configurados');

        this.carregarAreas();
        console.log('AreasObservacao constructor finalizado');
    }

    detectBaseUrl() {
        // Detectar o prefixo da URL baseado no pathname atual
        const path = window.location.pathname;
        if (path.startsWith('/integracity')) {
            return '/integracity';
        }
        return '';
    }

    initDrawControl() {
        // Configuração das ferramentas de desenho
        this.drawControl = new L.Control.Draw({
            position: 'topright',
            draw: {
                polyline: false,
                circle: false,
                circlemarker: false,
                marker: false,
                polygon: {
                    allowIntersection: false,
                    drawError: {
                        color: '#e74c3c',
                        message: '<strong>Erro:</strong> Linhas não podem se cruzar!'
                    },
                    shapeOptions: {
                        color: '#00D4FF',
                        fillColor: '#00D4FF',
                        fillOpacity: 0.2,
                        weight: 2
                    },
                    showArea: true,
                    metric: true
                },
                rectangle: {
                    shapeOptions: {
                        color: '#00D4FF',
                        fillColor: '#00D4FF',
                        fillOpacity: 0.2,
                        weight: 2
                    },
                    showArea: true,
                    metric: true
                }
            },
            edit: {
                featureGroup: this.drawnItems,
                remove: true
            }
        });

        this.map.addControl(this.drawControl);

        // Traduzir textos do Leaflet.draw
        L.drawLocal.draw.toolbar.buttons.polygon = 'Desenhar área poligonal';
        L.drawLocal.draw.toolbar.buttons.rectangle = 'Desenhar área retangular';
        L.drawLocal.draw.handlers.polygon.tooltip.start = 'Clique para começar a desenhar';
        L.drawLocal.draw.handlers.polygon.tooltip.cont = 'Clique para continuar desenhando';
        L.drawLocal.draw.handlers.polygon.tooltip.end = 'Clique no primeiro ponto para fechar';
        L.drawLocal.draw.handlers.rectangle.tooltip.start = 'Clique e arraste para desenhar';
        L.drawLocal.edit.toolbar.buttons.edit = 'Editar áreas';
        L.drawLocal.edit.toolbar.buttons.remove = 'Remover áreas';
    }

    initEventHandlers() {
        // Evento quando uma área é criada
        this.map.on(L.Draw.Event.CREATED, (e) => {
            const layer = e.layer;
            const type = e.layerType;

            this.drawnItems.addLayer(layer);
            this.abrirModalNomearArea(layer, type);
        });

        // Evento quando uma área é editada
        this.map.on(L.Draw.Event.EDITED, (e) => {
            const layers = e.layers;
            layers.eachLayer((layer) => {
                if (layer.areaId) {
                    this.atualizarArea(layer);
                }
            });
        });

        // Evento quando uma área é deletada
        this.map.on(L.Draw.Event.DELETED, (e) => {
            const layers = e.layers;
            layers.eachLayer((layer) => {
                if (layer.areaId) {
                    this.deletarArea(layer.areaId);
                }
            });
        });
    }

    abrirModalNomearArea(layer, type) {
        // Criar modal para nomear a área
        const modalHtml = `
            <div class="modal fade" id="modalNomearArea" tabindex="-1" data-bs-backdrop="static">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content bg-dark text-white">
                        <div class="modal-header border-secondary">
                            <h5 class="modal-title">
                                <i class="fas fa-draw-polygon me-2"></i>Nova Área de Observação
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label">Nome da Área *</label>
                                <input type="text" class="form-control bg-dark text-white border-secondary"
                                       id="areaNome" placeholder="Ex: Zona Sul - Copacabana" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Descrição</label>
                                <textarea class="form-control bg-dark text-white border-secondary"
                                          id="areaDescricao" rows="3"
                                          placeholder="Descrição opcional da área"></textarea>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Cor no Mapa</label>
                                <div class="d-flex gap-2 flex-wrap" id="corSelector">
                                    <button type="button" class="btn-cor active" data-cor="#00D4FF"
                                            style="background:#00D4FF"></button>
                                    <button type="button" class="btn-cor" data-cor="#FF6B35"
                                            style="background:#FF6B35"></button>
                                    <button type="button" class="btn-cor" data-cor="#7B2CBF"
                                            style="background:#7B2CBF"></button>
                                    <button type="button" class="btn-cor" data-cor="#00C853"
                                            style="background:#00C853"></button>
                                    <button type="button" class="btn-cor" data-cor="#FFD93D"
                                            style="background:#FFD93D"></button>
                                    <button type="button" class="btn-cor" data-cor="#FF1744"
                                            style="background:#FF1744"></button>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Vincular a Evento (opcional)</label>
                                <select class="form-select bg-dark text-white border-secondary" id="areaEvento">
                                    <option value="">-- Nenhum evento --</option>
                                </select>
                            </div>
                        </div>
                        <div class="modal-footer border-secondary">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="btnCancelarArea">
                                <i class="fas fa-times me-1"></i>Cancelar
                            </button>
                            <button type="button" class="btn btn-primary" id="btnSalvarArea">
                                <i class="fas fa-save me-1"></i>Salvar Área
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remover modal anterior se existir
        const modalAnterior = document.getElementById('modalNomearArea');
        if (modalAnterior) {
            modalAnterior.remove();
        }

        // Adicionar modal ao DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        const modal = new bootstrap.Modal(document.getElementById('modalNomearArea'));

        // Carregar eventos ativos
        this.carregarEventos();

        // Event listeners
        document.querySelectorAll('.btn-cor').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.btn-cor').forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                // Atualizar cor do layer
                const cor = this.dataset.cor;
                layer.setStyle({
                    color: cor,
                    fillColor: cor
                });
            });
        });

        document.getElementById('btnSalvarArea').addEventListener('click', () => {
            this.salvarArea(layer, type, modal);
        });

        document.getElementById('btnCancelarArea').addEventListener('click', () => {
            this.drawnItems.removeLayer(layer);
        });

        // Remover layer se modal for fechado sem salvar
        document.getElementById('modalNomearArea').addEventListener('hidden.bs.modal', () => {
            if (!layer.areaId) {
                this.drawnItems.removeLayer(layer);
            }
            document.getElementById('modalNomearArea').remove();
        });

        modal.show();
        document.getElementById('areaNome').focus();
    }

    async carregarEventos() {
        try {
            const response = await fetch(`${this.baseUrl}/api/eventos/`);
            if (response.ok) {
                const eventos = await response.json();
                const select = document.getElementById('areaEvento');
                eventos.forEach(evento => {
                    const option = document.createElement('option');
                    option.value = evento.id;
                    option.textContent = evento.nome;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.log('Nenhum evento disponível');
        }
    }

    async salvarArea(layer, type, modal) {
        const nome = document.getElementById('areaNome').value.trim();
        const descricao = document.getElementById('areaDescricao').value.trim();
        const corAtiva = document.querySelector('.btn-cor.active');
        const cor = corAtiva ? corAtiva.dataset.cor : '#00D4FF';
        const eventoId = document.getElementById('areaEvento').value;

        if (!nome) {
            this.mostrarNotificacao('Por favor, informe o nome da área', 'warning');
            document.getElementById('areaNome').focus();
            return;
        }

        // Converter layer para GeoJSON
        const geojson = layer.toGeoJSON();

        const dados = {
            nome: nome,
            descricao: descricao,
            cor: cor,
            geojson: geojson.geometry,
            tipo_desenho: type === 'rectangle' ? 'rectangle' : 'polygon',
            evento_id: eventoId || null
        };

        try {
            const response = await fetch(`${this.baseUrl}/api/areas/criar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(dados)
            });

            if (response.ok) {
                const resultado = await response.json();

                // Atualizar layer com ID da área
                layer.areaId = resultado.id;
                layer.areaNome = nome;

                // Mover para camada de áreas salvas
                this.drawnItems.removeLayer(layer);
                this.areasLayer.addLayer(layer);

                // Adicionar popup
                this.adicionarPopupArea(layer, resultado);

                modal.hide();
                this.mostrarNotificacao(`Área "${nome}" criada com sucesso!`, 'success');

                // Atualizar inventário imediatamente
                this.inventariarArea(resultado.id);

            } else {
                const erro = await response.json();
                this.mostrarNotificacao(erro.error || 'Erro ao salvar área', 'danger');
            }
        } catch (error) {
            console.error('Erro ao salvar área:', error);
            this.mostrarNotificacao('Erro de conexão ao salvar área', 'danger');
        }
    }

    async atualizarArea(layer) {
        const geojson = layer.toGeoJSON();

        try {
            const response = await fetch(`${this.baseUrl}/api/areas/${layer.areaId}/atualizar/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    geojson: geojson.geometry
                })
            });

            if (response.ok) {
                this.mostrarNotificacao('Área atualizada com sucesso!', 'success');
                this.inventariarArea(layer.areaId);
            } else {
                this.mostrarNotificacao('Erro ao atualizar área', 'danger');
            }
        } catch (error) {
            console.error('Erro ao atualizar área:', error);
        }
    }

    async deletarArea(areaId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/areas/${areaId}/deletar/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                this.mostrarNotificacao('Área removida com sucesso!', 'success');
            } else {
                this.mostrarNotificacao('Erro ao remover área', 'danger');
            }
        } catch (error) {
            console.error('Erro ao deletar área:', error);
        }
    }

    async carregarAreas() {
        try {
            const response = await fetch(`${this.baseUrl}/api/areas/listar/`);
            if (response.ok) {
                const areas = await response.json();
                this.areasSalvas = areas;

                areas.forEach(area => {
                    this.desenharArea(area);
                });
            }
        } catch (error) {
            console.error('Erro ao carregar áreas:', error);
        }
    }

    desenharArea(area) {
        const geojson = area.geojson;

        // Converter coordenadas GeoJSON para Leaflet
        let layer;

        if (geojson.type === 'Polygon') {
            // GeoJSON usa [lng, lat], Leaflet usa [lat, lng]
            const latlngs = geojson.coordinates[0].map(coord => [coord[1], coord[0]]);
            layer = L.polygon(latlngs, {
                color: area.cor,
                fillColor: area.cor,
                fillOpacity: 0.2,
                weight: 2
            });
        }

        if (layer) {
            layer.areaId = area.id;
            layer.areaNome = area.nome;

            this.areasLayer.addLayer(layer);
            this.adicionarPopupArea(layer, area);
        }
    }

    adicionarPopupArea(layer, area) {
        const nivelClasses = {
            'E1': 'bg-success',
            'E2': 'bg-info',
            'E3': 'bg-warning text-dark',
            'E4': 'bg-danger',
            'E5': 'bg-dark'
        };

        const nivelClass = nivelClasses[area.nivel_operacional] || 'bg-secondary';

        const popupContent = `
            <div class="area-popup">
                <h6 class="mb-2">
                    <i class="fas fa-draw-polygon me-1" style="color:${area.cor}"></i>
                    ${area.nome}
                </h6>
                ${area.descricao ? `<p class="small text-muted mb-2">${area.descricao}</p>` : ''}
                <div class="d-flex align-items-center gap-2 mb-2">
                    <span class="badge ${nivelClass}">${area.nivel_operacional}</span>
                    <small class="text-muted">Nível Operacional</small>
                </div>
                <div class="btn-group btn-group-sm w-100">
                    <a href="${this.baseUrl}/areas/${area.id}/" target="_blank" class="btn btn-outline-primary">
                        <i class="fas fa-eye"></i> Detalhes
                    </a>
                    <button class="btn btn-outline-info" onclick="areasObservacao.inventariarArea('${area.id}')">
                        <i class="fas fa-sync"></i> Atualizar
                    </button>
                </div>
            </div>
        `;

        layer.bindPopup(popupContent, {
            maxWidth: 300,
            className: 'area-popup-container'
        });
    }

    async inventariarArea(areaId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/areas/${areaId}/inventariar/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                const inventario = await response.json();
                console.log('Inventário atualizado:', inventario);

                // Atualizar popup se a área estiver visível
                this.areasLayer.eachLayer(layer => {
                    if (layer.areaId === areaId) {
                        this.adicionarPopupArea(layer, {
                            ...inventario.area,
                            nivel_operacional: inventario.nivel_operacional
                        });
                    }
                });
            }
        } catch (error) {
            console.error('Erro ao inventariar área:', error);
        }
    }

    focalizarArea(areaId) {
        this.areasLayer.eachLayer(layer => {
            if (layer.areaId === areaId) {
                this.map.fitBounds(layer.getBounds(), { padding: [50, 50] });
                layer.openPopup();
            }
        });
    }

    toggleVisibilidade(areaId, visivel) {
        this.areasLayer.eachLayer(layer => {
            if (layer.areaId === areaId) {
                if (visivel) {
                    layer.setStyle({ opacity: 1, fillOpacity: 0.2 });
                } else {
                    layer.setStyle({ opacity: 0, fillOpacity: 0 });
                }
            }
        });
    }

    getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }

    mostrarNotificacao(mensagem, tipo = 'info') {
        // Usar sistema de notificação existente se disponível
        if (typeof showNotification === 'function') {
            showNotification(mensagem, tipo);
        } else if (typeof toastr !== 'undefined') {
            toastr[tipo](mensagem);
        } else {
            // Fallback para alert
            const toast = document.createElement('div');
            toast.className = `toast-notification toast-${tipo}`;
            toast.innerHTML = `
                <div class="toast-content">
                    <i class="fas fa-${tipo === 'success' ? 'check-circle' : tipo === 'danger' ? 'exclamation-circle' : 'info-circle'}"></i>
                    <span>${mensagem}</span>
                </div>
            `;
            document.body.appendChild(toast);

            setTimeout(() => toast.classList.add('show'), 100);
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }
    }
}

// Estilos CSS inline para o sistema
const areasStyles = `
    .btn-cor {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        border: 2px solid transparent;
        cursor: pointer;
        transition: all 0.2s;
    }
    .btn-cor:hover {
        transform: scale(1.1);
    }
    .btn-cor.active {
        border-color: #fff;
        box-shadow: 0 0 0 2px rgba(0,212,255,0.5);
    }
    .area-popup h6 {
        font-weight: 600;
    }
    .area-popup-container .leaflet-popup-content-wrapper {
        background: rgba(30, 30, 45, 0.95);
        color: #fff;
        border-radius: 8px;
    }
    .area-popup-container .leaflet-popup-tip {
        background: rgba(30, 30, 45, 0.95);
    }
    .toast-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        background: rgba(30, 30, 45, 0.95);
        color: #fff;
        z-index: 10000;
        transform: translateX(100%);
        opacity: 0;
        transition: all 0.3s ease;
    }
    .toast-notification.show {
        transform: translateX(0);
        opacity: 1;
    }
    .toast-success { border-left: 4px solid #00C853; }
    .toast-danger { border-left: 4px solid #FF1744; }
    .toast-warning { border-left: 4px solid #FFD93D; }
    .toast-info { border-left: 4px solid #00D4FF; }
    .toast-content {
        display: flex;
        align-items: center;
        gap: 10px;
    }
`;

// Injetar estilos
if (!document.getElementById('areas-observacao-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'areas-observacao-styles';
    styleSheet.textContent = areasStyles;
    document.head.appendChild(styleSheet);
}

// Variável global para acesso
let areasObservacao = null;

// Inicializar quando o mapa estiver pronto
function initAreasObservacao(map) {
    areasObservacao = new AreasObservacao(map);
    return areasObservacao;
}
