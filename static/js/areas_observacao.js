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
            console.log('=== EVENTO CREATED RECEBIDO ===');
            console.log('Layer:', e.layer);
            console.log('Type:', e.layerType);

            const layer = e.layer;
            const type = e.layerType;

            this.drawnItems.addLayer(layer);
            console.log('Layer adicionado ao drawnItems');

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
        console.log('=== ABRINDO MODAL ===');
        console.log('Layer recebido:', layer);
        console.log('Type:', type);

        // Guardar referência ao layer atual
        this.currentLayer = layer;
        this.currentType = type;

        // Usar prompt nativo do JavaScript - mais confiável
        this.abrirPromptSimples(layer, type);
    }

    async abrirPromptSimples(layer, type) {
        // Usar prompt nativo do JavaScript - funciona em qualquer navegador
        const nome = prompt('Digite o nome da área de observação:', '');

        if (!nome || nome.trim() === '') {
            // Usuário cancelou ou não digitou nada
            this.drawnItems.removeLayer(layer);
            this.mostrarNotificacao('Criação de área cancelada', 'warning');
            return;
        }

        const descricao = prompt('Digite uma descrição (opcional):', '') || '';

        // Cor padrão
        const cor = '#00D4FF';

        // Converter layer para GeoJSON
        const geojson = layer.toGeoJSON();

        const dados = {
            nome: nome.trim(),
            descricao: descricao.trim(),
            cor: cor,
            geojson: geojson.geometry,
            tipo_desenho: type === 'rectangle' ? 'rectangle' : 'polygon'
        };

        try {
            this.mostrarNotificacao('Salvando área...', 'info');

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
                console.log('Área salva com sucesso:', resultado);

                // Atualizar layer
                layer.areaId = resultado.area_id;
                layer.areaNome = nome;

                // Mover para camada de áreas salvas
                this.drawnItems.removeLayer(layer);
                this.areasLayer.addLayer(layer);

                // Adicionar popup
                this.adicionarPopupArea(layer, resultado);

                this.mostrarNotificacao(`Área "${nome}" criada com sucesso!`, 'success');

                // Recarregar página para mostrar na lista
                setTimeout(() => location.reload(), 1500);

            } else {
                const erro = await response.json();
                alert('Erro ao salvar: ' + (erro.error || 'Erro desconhecido'));
                this.drawnItems.removeLayer(layer);
            }
        } catch (error) {
            console.error('Erro ao salvar área:', error);
            alert('Erro de conexão ao salvar área. Verifique sua conexão.');
            this.drawnItems.removeLayer(layer);
        }
    }

    abrirModalBootstrap(layer, type) {
        // Usar modal existente no DOM
        const modalElement = document.getElementById('modalNomearArea');
        if (!modalElement) {
            console.error('Modal não encontrado no DOM!');
            this.abrirModalCustomizado(layer, type);
            return;
        }

        // Limpar campos
        document.getElementById('areaNome').value = '';
        document.getElementById('areaDescricao').value = '';

        // Resetar cor selecionada
        document.querySelectorAll('.btn-cor').forEach(btn => {
            btn.style.border = '2px solid transparent';
        });
        const firstColor = document.querySelector('.btn-cor');
        if (firstColor) {
            firstColor.style.border = '2px solid #fff';
            firstColor.classList.add('active');
        }

        // Configurar eventos do modal
        this.setupModalEvents(layer, type);

        // Abrir modal
        const modal = new bootstrap.Modal(modalElement);
        modal.show();

        // Focar no campo nome
        setTimeout(() => {
            document.getElementById('areaNome').focus();
        }, 300);
    }

    abrirModalCustomizado(layer, type) {
        // Remover modal anterior se existir
        const existingModal = document.getElementById('customModalNomearArea');
        if (existingModal) existingModal.remove();

        // Criar modal customizado
        const modalHtml = `
            <div id="customModalNomearArea" class="custom-modal-overlay">
                <div class="custom-modal-dialog">
                    <div class="custom-modal-content">
                        <div class="custom-modal-header">
                            <h5><i class="fas fa-draw-polygon"></i> Nova Área de Observação</h5>
                            <button type="button" class="custom-modal-close" id="customModalClose">&times;</button>
                        </div>
                        <div class="custom-modal-body">
                            <div class="form-group">
                                <label for="customAreaNome">Nome da Área *</label>
                                <input type="text" id="customAreaNome" name="customAreaNome" class="custom-input"
                                       placeholder="Ex: Zona Sul - Copacabana" required tabindex="1" autocomplete="off">
                            </div>
                            <div class="form-group">
                                <label for="customAreaDescricao">Descrição</label>
                                <textarea id="customAreaDescricao" name="customAreaDescricao" class="custom-input"
                                          rows="3" placeholder="Descrição opcional da área" tabindex="2"></textarea>
                            </div>
                            <div class="form-group">
                                <label>Cor no Mapa</label>
                                <div class="color-selector" id="customCorSelector">
                                    <button type="button" class="custom-btn-cor active" data-cor="#00D4FF" style="background:#00D4FF"></button>
                                    <button type="button" class="custom-btn-cor" data-cor="#FF6B35" style="background:#FF6B35"></button>
                                    <button type="button" class="custom-btn-cor" data-cor="#7B2CBF" style="background:#7B2CBF"></button>
                                    <button type="button" class="custom-btn-cor" data-cor="#00C853" style="background:#00C853"></button>
                                    <button type="button" class="custom-btn-cor" data-cor="#FFD93D" style="background:#FFD93D"></button>
                                    <button type="button" class="custom-btn-cor" data-cor="#FF1744" style="background:#FF1744"></button>
                                </div>
                            </div>
                        </div>
                        <div class="custom-modal-footer">
                            <button type="button" class="custom-btn custom-btn-secondary" id="customBtnCancelar">
                                <i class="fas fa-times"></i> Cancelar
                            </button>
                            <button type="button" class="custom-btn custom-btn-primary" id="customBtnSalvar">
                                <i class="fas fa-save"></i> Salvar Área
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Adicionar estilos do modal customizado
        this.injectCustomModalStyles();

        // Adicionar ao DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        const modal = document.getElementById('customModalNomearArea');
        const self = this;

        // Eventos de cor
        document.querySelectorAll('.custom-btn-cor').forEach(btn => {
            btn.onclick = function() {
                document.querySelectorAll('.custom-btn-cor').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                const cor = this.dataset.cor;
                layer.setStyle({ color: cor, fillColor: cor });
            };
        });

        // Botão salvar
        document.getElementById('customBtnSalvar').onclick = function() {
            self.salvarAreaCustomModal(layer, type, modal);
        };

        // Botão cancelar
        document.getElementById('customBtnCancelar').onclick = function() {
            self.drawnItems.removeLayer(layer);
            modal.remove();
        };

        // Botão fechar
        document.getElementById('customModalClose').onclick = function() {
            self.drawnItems.removeLayer(layer);
            modal.remove();
        };

        // Fechar ao clicar fora (apenas no overlay, não no conteúdo)
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                self.drawnItems.removeLayer(layer);
                modal.remove();
            }
        });

        // Prevenir que cliques no conteúdo fechem o modal
        const dialogContent = modal.querySelector('.custom-modal-dialog');
        if (dialogContent) {
            dialogContent.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }

        // Mostrar modal com animação
        setTimeout(() => {
            modal.classList.add('show');
            const nomeInput = document.getElementById('customAreaNome');
            if (nomeInput) {
                nomeInput.focus();
                nomeInput.click();
            }
        }, 50);
    }

    async salvarAreaCustomModal(layer, type, modal) {
        const nome = document.getElementById('customAreaNome').value.trim();
        const descricao = document.getElementById('customAreaDescricao').value.trim();
        const corAtiva = document.querySelector('.custom-btn-cor.active');
        const cor = corAtiva ? corAtiva.dataset.cor : '#00D4FF';

        if (!nome) {
            alert('Por favor, informe o nome da área');
            document.getElementById('customAreaNome').focus();
            return;
        }

        // Converter layer para GeoJSON
        const geojson = layer.toGeoJSON();

        const dados = {
            nome: nome,
            descricao: descricao,
            cor: cor,
            geojson: geojson.geometry,
            tipo_desenho: type === 'rectangle' ? 'rectangle' : 'polygon'
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
                console.log('Área salva com sucesso:', resultado);

                // Atualizar layer
                layer.areaId = resultado.area_id;
                layer.areaNome = nome;

                // Mover para camada de áreas salvas
                this.drawnItems.removeLayer(layer);
                this.areasLayer.addLayer(layer);

                // Adicionar popup
                this.adicionarPopupArea(layer, resultado);

                // Fechar modal
                modal.remove();

                this.mostrarNotificacao(`Área "${nome}" criada com sucesso!`, 'success');

                // Recarregar página para mostrar na lista
                setTimeout(() => location.reload(), 1000);

            } else {
                const erro = await response.json();
                alert(erro.error || 'Erro ao salvar área');
            }
        } catch (error) {
            console.error('Erro ao salvar área:', error);
            alert('Erro de conexão ao salvar área');
        }
    }

    injectCustomModalStyles() {
        if (document.getElementById('custom-modal-styles')) return;

        const styles = `
            .custom-modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            .custom-modal-overlay.show {
                opacity: 1;
            }
            .custom-modal-dialog {
                width: 90%;
                max-width: 450px;
                transform: scale(0.9);
                transition: transform 0.3s ease;
                position: relative;
                z-index: 10001;
            }
            .custom-modal-overlay.show .custom-modal-dialog {
                transform: scale(1);
            }
            .custom-modal-content {
                background: #1e1e2d;
                border-radius: 12px;
                overflow: visible;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                border: 1px solid #333;
                position: relative;
            }
            .custom-modal-header {
                padding: 20px;
                border-bottom: 1px solid #333;
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: relative;
            }
            .custom-modal-header h5 {
                margin: 0;
                color: #fff;
                font-size: 1.1rem;
            }
            .custom-modal-header h5 i {
                color: #00D4FF;
                margin-right: 10px;
            }
            .custom-modal-close {
                background: none;
                border: none;
                color: #888;
                font-size: 24px;
                cursor: pointer;
                line-height: 1;
                z-index: 10003;
            }
            .custom-modal-close:hover {
                color: #fff;
            }
            .custom-modal-body {
                padding: 20px;
                position: relative;
                z-index: 10002;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                color: #aaa;
                margin-bottom: 8px;
                font-size: 0.9rem;
            }
            .custom-input {
                width: 100%;
                padding: 12px;
                background: #2a2a3e;
                border: 1px solid #444;
                border-radius: 8px;
                color: #fff;
                font-size: 1rem;
                box-sizing: border-box;
                position: relative;
                z-index: 10002;
                pointer-events: auto !important;
                -webkit-user-select: text !important;
                user-select: text !important;
            }
            .custom-input:focus {
                outline: none;
                border-color: #00D4FF;
                box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
            }
            textarea.custom-input {
                resize: vertical;
                min-height: 80px;
            }
            .color-selector {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            .custom-btn-cor {
                width: 36px;
                height: 36px;
                border-radius: 50%;
                border: 3px solid transparent;
                cursor: pointer;
                transition: all 0.2s;
            }
            .custom-btn-cor:hover {
                transform: scale(1.15);
            }
            .custom-btn-cor.active {
                border-color: #fff;
                box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
            }
            .custom-modal-footer {
                padding: 15px 20px;
                border-top: 1px solid #333;
                display: flex;
                justify-content: flex-end;
                gap: 10px;
            }
            .custom-btn {
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
                cursor: pointer;
                font-size: 0.9rem;
                display: flex;
                align-items: center;
                gap: 8px;
                transition: all 0.2s;
            }
            .custom-btn-secondary {
                background: #444;
                color: #fff;
            }
            .custom-btn-secondary:hover {
                background: #555;
            }
            .custom-btn-primary {
                background: #00D4FF;
                color: #000;
                font-weight: 600;
            }
            .custom-btn-primary:hover {
                background: #00b8e6;
                box-shadow: 0 4px 15px rgba(0, 212, 255, 0.4);
            }
        `;

        const styleEl = document.createElement('style');
        styleEl.id = 'custom-modal-styles';
        styleEl.textContent = styles;
        document.head.appendChild(styleEl);
    }

    setupModalEvents(layer, type) {
        const self = this;

        // Eventos de cor
        document.querySelectorAll('.btn-cor').forEach(btn => {
            btn.onclick = function() {
                document.querySelectorAll('.btn-cor').forEach(b => {
                    b.style.border = '2px solid transparent';
                    b.classList.remove('active');
                });
                this.style.border = '2px solid #fff';
                this.classList.add('active');

                // Atualizar cor do layer
                const cor = this.dataset.cor;
                layer.setStyle({ color: cor, fillColor: cor });
            };
        });

        // Botão salvar
        document.getElementById('btnSalvarArea').onclick = function() {
            self.salvarAreaDoModal(layer, type);
        };

        // Botão cancelar - remover layer
        document.getElementById('btnCancelarArea').onclick = function() {
            self.drawnItems.removeLayer(layer);
        };

        // Quando modal fecha sem salvar
        const modalElement = document.getElementById('modalNomearArea');
        modalElement.addEventListener('hidden.bs.modal', function handler() {
            if (!layer.areaId) {
                self.drawnItems.removeLayer(layer);
            }
            modalElement.removeEventListener('hidden.bs.modal', handler);
        });
    }

    async salvarAreaDoModal(layer, type) {
        const nome = document.getElementById('areaNome').value.trim();
        const descricao = document.getElementById('areaDescricao').value.trim();
        const corAtiva = document.querySelector('.btn-cor.active');
        const cor = corAtiva ? corAtiva.dataset.cor : '#00D4FF';

        if (!nome) {
            alert('Por favor, informe o nome da área');
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
            tipo_desenho: type === 'rectangle' ? 'rectangle' : 'polygon'
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
                console.log('Área salva com sucesso:', resultado);

                // Atualizar layer
                layer.areaId = resultado.area_id;
                layer.areaNome = nome;

                // Mover para camada de áreas salvas
                this.drawnItems.removeLayer(layer);
                this.areasLayer.addLayer(layer);

                // Adicionar popup
                this.adicionarPopupArea(layer, resultado);

                // Fechar modal
                const modalElement = document.getElementById('modalNomearArea');
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) modal.hide();

                this.mostrarNotificacao(`Área "${nome}" criada com sucesso!`, 'success');

                // Recarregar página para mostrar na lista
                setTimeout(() => location.reload(), 1000);

            } else {
                const erro = await response.json();
                alert(erro.error || 'Erro ao salvar área');
            }
        } catch (error) {
            console.error('Erro ao salvar área:', error);
            alert('Erro de conexão ao salvar área');
        }
    }

    // MÉTODO ANTIGO - MANTIDO PARA COMPATIBILIDADE
    _abrirModalNomearArea_OLD(layer, type) {
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
        console.log('Modal HTML adicionado ao DOM');

        const modalElement = document.getElementById('modalNomearArea');
        console.log('Modal element:', modalElement);

        const modal = new bootstrap.Modal(modalElement);
        console.log('Bootstrap Modal criado:', modal);

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
                layer.areaId = resultado.area_id;
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
                const data = await response.json();

                // API retorna {success: true, areas: [...], total: N}
                if (data.success && data.areas) {
                    this.areasSalvas = data.areas;

                    data.areas.forEach(area => {
                        this.desenharArea(area);
                    });

                    console.log(`${data.areas.length} área(s) carregada(s) do servidor`);
                }
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
