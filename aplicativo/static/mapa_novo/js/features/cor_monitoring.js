/**
 * cor_monitoring.js - Painel de Monitoramento Inferior
 */

class MonitoringPanel {
    constructor() {
        this.panel = document.querySelector('.cor-monitoring-panel');
        this.toggle = document.getElementById('monitoring-toggle'); // ✅ CORRIGIDO: era querySelector
        this.init();
    }

    init() {
        this.loadMonitoringData();
        setInterval(() => this.loadMonitoringData(), 30000);

        if (this.toggle) {
            this.toggle.addEventListener('click', () => this.togglePanel());
            console.log('✅ Botão de toggle conectado');
        } else {
            console.error('❌ Botão monitoring-toggle não encontrado');
        }

        this.observeAlertsPanel();
    }

    async loadMonitoringData() {
        try {
            const [estagioData, ocorrenciasData, sirenesData] = await Promise.all([
                fetch('/api/estagio/').then(r => r.json()).catch(() => ({ success: false })),
                fetch('/api/ocorrencias/tempo-real/').then(r => r.json()).catch(() => ({ success: false })),
                fetch('/api/sirenes/').then(r => r.json()).catch(() => ({ success: false }))
            ]);

            this.updateCard('estagio', estagioData);
            this.updateCard('ocorrencias', ocorrenciasData);
            this.updateCard('sirenes', sirenesData);
            this.updateProgressBar();

        } catch (error) {
            console.error('Erro ao carregar dados de monitoramento:', error);
        }
    }

    updateCard(type, data) {
        const card = document.querySelector('[data-card="' + type + '"]');
        if (!card) return;

        try {
            if (type === 'estagio' && data && data.success) {
                const estagio_texto = data.estagio || 'Nível 1';
                const cor = data.cor || '#94c842';

                const match = estagio_texto.match(/(\d+)/);
                const nivel = match ? parseInt(match[1]) : 1;

                const valueEl = card.querySelector('.cor-status-card-value');
                const subtitleEl = card.querySelector('.cor-status-card-subtitle');

                if (valueEl) valueEl.textContent = estagio_texto;
                if (subtitleEl) {
                    const descricoes = {
                        1: 'Normalidade',
                        2: 'Atenção',
                        3: 'Alerta',
                        4: 'Alerta Máximo',
                        5: 'Crise'
                    };
                    subtitleEl.textContent = descricoes[nivel] || 'Normalidade';
                }

                card.style.borderLeftColor = cor;
                card.className = 'cor-status-card nivel-' + nivel;
            }

            if (type === 'ocorrencias' && data && data.success) {
                const count = (data.data && Array.isArray(data.data)) ? data.data.length : 0;
                const valueEl = card.querySelector('.cor-status-card-value');

                if (valueEl) valueEl.textContent = count;

                const nivel = count === 0 ? 0 : count < 5 ? 1 : count < 10 ? 2 : 3;
                card.className = 'cor-status-card nivel-' + nivel;
            }

            if (type === 'sirenes' && data && data.success) {
                const dataArray = (data.data && Array.isArray(data.data)) ? data.data : [];
                const active = dataArray.filter(s => s && s.status === 'ativa').length;
                const valueEl = card.querySelector('.cor-status-card-value');

                if (valueEl) valueEl.textContent = active;

                const nivel = active === 0 ? 0 : active < 3 ? 2 : 3;
                card.className = 'cor-status-card nivel-' + nivel;
            }
        } catch (error) {
            console.error('Erro ao atualizar card ' + type + ':', error);
        }
    }

    updateProgressBar() {
        const progressBar = document.querySelector('.cor-progress-bar');
        const percentageEl = document.querySelector('.cor-progress-percentage');

        if (!progressBar) return;

        const now = new Date();
        const hour = now.getHours();
        let percentage = 50;

        if ((hour >= 7 && hour <= 9) || (hour >= 17 && hour <= 19)) {
            percentage = 75 + Math.random() * 25;
        } else if (hour >= 22 || hour <= 6) {
            percentage = 10 + Math.random() * 20;
        } else {
            percentage = 40 + Math.random() * 30;
        }

        progressBar.style.width = percentage + '%';
        if (percentageEl) percentageEl.textContent = Math.round(percentage) + '%';
    }

    togglePanel() {
        this.panel.classList.toggle('collapsed');
        this.toggle.classList.toggle('panel-collapsed');

        const icon = this.toggle.querySelector('i');
        const text = this.toggle.querySelector('span');
        const mapElement = document.getElementById('map'); // ← NOVO

        if (this.panel.classList.contains('collapsed')) {
            icon.className = 'bi bi-chevron-up';
            if (text) text.textContent = 'Mostrar Monitoramento';
            if (mapElement) mapElement.classList.add('monitoring-collapsed'); // ← NOVO
            console.log('📽 Painel fechado');
        } else {
            icon.className = 'bi bi-chevron-down';
            if (text) text.textContent = 'Ocultar Monitoramento';
            if (mapElement) mapElement.classList.remove('monitoring-collapsed'); // ← NOVO
            console.log('📼 Painel aberto');
        }

        setTimeout(() => {
            if (typeof map !== 'undefined') {
                map.invalidateSize();
                console.log('🗺️ Mapa redimensionado');
            }
        }, 300);
    }

    observeAlertsPanel() {
        const alertsPanel = document.getElementById('alerts-panel');
        if (!alertsPanel) return;

        const observer = new MutationObserver(() => {
            if (alertsPanel.classList.contains('collapsed')) {
                this.panel.classList.add('alerts-collapsed');
            } else {
                this.panel.classList.remove('alerts-collapsed');
            }

            setTimeout(() => {
                if (typeof map !== 'undefined') {
                    map.invalidateSize();
                }
            }, 300);
        });

        observer.observe(alertsPanel, {
            attributes: true,
            attributeFilter: ['class']
        });

        if (alertsPanel.classList.contains('collapsed')) {
            this.panel.classList.add('alerts-collapsed');
        }
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.monitoringPanel = new MonitoringPanel();
    });
} else {
    window.monitoringPanel = new MonitoringPanel();
}

console.log('✅ cor_monitoring.js carregado');

// ===== TODOS OS CARDS =====
async function loadCalorData() {
    try {
        const response = await fetch('/api/calor/');
        const data = await response.json();

        if (data.success) {
            const calorCard = document.querySelector('[data-card="calor"]');
            if (calorCard) {
                const labelElement = calorCard.querySelector('.cor-status-card-label');
                if (labelElement) labelElement.textContent = 'Calor ' + data.nivel;

                const valueElement = calorCard.querySelector('.cor-status-card-value');
                if (valueElement) valueElement.textContent = data.nivel;

                const subtitleElement = calorCard.querySelector('.cor-status-card-subtitle');
                if (subtitleElement) subtitleElement.textContent = data.nome;

                calorCard.classList.remove('nivel-0', 'nivel-1', 'nivel-2', 'nivel-3');
                calorCard.classList.add('nivel-' + data.nivel);
                calorCard.style.borderLeftColor = data.cor;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar dados de calor:', error);
    }
}

async function loadOcorrenciasCard() {
    try {
        const response = await fetch('/api/ocorrencias/');
        const data = await response.json();

        if (data.success) {
            const card = document.querySelector('[data-card="ocorrencias"]');
            if (card) {
                const valueElement = card.querySelector('.cor-status-card-value');
                if (valueElement) valueElement.textContent = data.count;

                card.classList.remove('nivel-0', 'nivel-1', 'nivel-2', 'nivel-3', 'nivel-4');
                let nivel = 0;
                if (data.count >= 50) nivel = 4;
                else if (data.count >= 30) nivel = 3;
                else if (data.count >= 15) nivel = 2;
                else if (data.count >= 5) nivel = 1;
                card.classList.add('nivel-' + nivel);
            }
        }
    } catch (error) {
        console.error('Erro ao carregar ocorrências:', error);
    }
}

async function loadEventosCard() {
    try {
        const response = await fetch('/api/eventos/');
        const data = await response.json();

        if (data.success) {
            const card = document.querySelector('[data-card="eventos"]');
            if (card) {
                const valueElement = card.querySelector('.cor-status-card-value');
                if (valueElement) valueElement.textContent = data.count;

                card.classList.remove('nivel-0', 'nivel-1', 'nivel-2', 'nivel-3');
                let nivel = 0;
                if (data.count >= 10) nivel = 2;
                else if (data.count >= 5) nivel = 1;
                card.classList.add('nivel-' + nivel);
            }
        }
    } catch (error) {
        console.error('Erro ao carregar eventos:', error);
    }
}

async function loadTempoCard() {
    try {
        const response = await fetch('/api/pluviometros/');
        const data = await response.json();

        if (data.success && data.data.length > 0) {
            const card = document.querySelector('[data-card="tempo"]');
            if (card) {
                let maxChuva = 0;
                data.data.forEach(p => {
                    if (p.chuva_1h > maxChuva) maxChuva = p.chuva_1h;
                });

                let nivel = 0, texto = 'N0', subtitulo = 'Estável';
                if (maxChuva >= 50) { nivel = 4; texto = 'N4'; subtitulo = 'Chuva Forte'; }
                else if (maxChuva >= 25) { nivel = 3; texto = 'N3'; subtitulo = 'Chuva Moderada'; }
                else if (maxChuva >= 10) { nivel = 2; texto = 'N2'; subtitulo = 'Chuva Leve'; }
                else if (maxChuva > 0) { nivel = 1; texto = 'N1'; subtitulo = 'Garoa'; }

                card.classList.remove('nivel-0', 'nivel-1', 'nivel-2', 'nivel-3', 'nivel-4');
                card.classList.add('nivel-' + nivel);

                const valueElement = card.querySelector('.cor-status-card-value');
                if (valueElement) valueElement.textContent = texto;

                const subtitleElement = card.querySelector('.cor-status-card-subtitle');
                if (subtitleElement) subtitleElement.textContent = subtitulo;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar tempo:', error);
    }
}

async function loadMobilidadeCard() {
    try {
        const response = await fetch('/api/estagio/');
        const data = await response.json();

        if (data.success) {
            const card = document.querySelector('[data-card="mobilidade"]');
            if (card) {
                const nivel = data.data.nivel || 1;
                card.classList.remove('nivel-0', 'nivel-1', 'nivel-2', 'nivel-3', 'nivel-4', 'nivel-5');
                card.classList.add('nivel-' + nivel);

                const valueElement = card.querySelector('.cor-status-card-value');
                if (valueElement) valueElement.textContent = 'N' + nivel;

                const subtitleElement = card.querySelector('.cor-status-card-subtitle');
                if (subtitleElement) {
                    const textos = { 1: 'Normal', 2: 'Atenção', 3: 'Alerta', 4: 'Crítico', 5: 'Crise' };
                    subtitleElement.textContent = textos[nivel] || 'Normal';
                }
            }
        }
    } catch (error) {
        console.error('Erro ao carregar mobilidade:', error);
    }
}

async function loadEstagioCard() {
    try {
        const response = await fetch('/api/estagio/');
        const data = await response.json();

        if (data.success && data.data) {
            const estagioCard = document.querySelector('[data-card="estagio"]');
            if (estagioCard) {
                const nivel = data.data.nivel || 1;

                const labelElement = estagioCard.querySelector('.cor-status-card-label');
                if (labelElement) labelElement.textContent = 'Estágio ' + nivel;

                const valueElement = estagioCard.querySelector('.cor-status-card-value');
                if (valueElement) valueElement.textContent = nivel;

                const subtitleElement = estagioCard.querySelector('.cor-status-card-subtitle');
                if (subtitleElement) subtitleElement.textContent = data.data.descricao || 'Normalidade';

                estagioCard.classList.remove('nivel-0', 'nivel-1', 'nivel-2', 'nivel-3', 'nivel-4', 'nivel-5');
                estagioCard.classList.add('nivel-' + nivel);

                if (data.data.cor) estagioCard.style.borderLeftColor = data.data.cor;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar estágio:', error);
    }
}

function initAllCards() {
    loadCalorData();
    loadEstagioCard();
    loadOcorrenciasCard();
    loadEventosCard();
    loadTempoCard();
    loadMobilidadeCard();
}

setTimeout(() => {
    initAllCards();
    setInterval(initAllCards, 30000);
}, 1000);