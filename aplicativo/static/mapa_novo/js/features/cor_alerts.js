/**
 * cor_alerts.js - Sistema de Alertas Dinâmico
 */

class AlertsManager {
    constructor() {
        this.alertsList = document.querySelector('.cor-alerts-list');
        this.alertsBadge = document.querySelector('.cor-alerts-badge');
        this.lastAlerts = [];
        this.init();
    }

    init() {
        this.loadAlerts();
        setInterval(() => this.loadAlerts(), 15000);
    }

    async loadAlerts() {
        try {
            const [ocorrenciasData, sirenesData] = await Promise.all([
                fetch('/api/ocorrencias/').then(r => r.json()),
                fetch('/api/sirenes/').then(r => r.json())
            ]);

            const alerts = [];

            if (ocorrenciasData.success && ocorrenciasData.data) {
                ocorrenciasData.data.slice(0, 5).forEach(oco => {
                    alerts.push({
                        id: 'oco-' + oco.id,
                        type: 'ocorrencia',
                        priority: oco.prioridade || 'media',
                        title: oco.descricao || 'Ocorrencia Registrada',
                        description: oco.tipo + ' - ' + (oco.status || 'Em andamento'),
                        time: this.formatTime(oco.data),
                        status: oco.status === 'fechada' ? 'confirmado' : 'apurando',
                        icon: 'bi-exclamation-triangle-fill',
                        lat: oco.lat,
                        lng: oco.lng
                    });
                });
            }

            if (sirenesData.success && sirenesData.data) {
                sirenesData.data
                    .filter(s => s.status === 'ativa' && s.prioridade === 'alta')
                    .slice(0, 3)
                    .forEach(sirene => {
                        alerts.push({
                            id: 'sir-' + sirene.id,
                            type: 'sirene',
                            priority: 'alta',
                            title: 'Sirene Ativada',
                            description: sirene.nome + ' - Alto risco',
                            time: this.formatTime(new Date()),
                            status: 'confirmado',
                            icon: 'bi-megaphone-fill',
                            lat: sirene.lat,
                            lng: sirene.lng
                        });
                    });
            }

            this.checkNewAlerts(alerts);
            this.renderAlerts(alerts);
            this.updateBadge(alerts.length);

        } catch (error) {
            console.error('Erro ao carregar alertas:', error);
        }
    }

    checkNewAlerts(currentAlerts) {
        const newAlerts = currentAlerts.filter(alert => 
            !this.lastAlerts.some(old => old.id === alert.id)
        );

        newAlerts.forEach(alert => {
            if (typeof notificationSystem !== 'undefined') {
                const notifType = alert.priority === 'alta' ? 'error' : 
                                 alert.priority === 'media' ? 'warning' : 'info';
                
                notificationSystem.show(
                    alert.title,
                    alert.description,
                    notifType
                );
            }
        });

        this.lastAlerts = currentAlerts;
    }

    renderAlerts(alerts) {
        if (alerts.length === 0) {
            this.alertsList.innerHTML = '<div style="text-align:center;padding:40px;color:#94a3b8"><i class="bi bi-check-circle" style="font-size:48px;margin-bottom:12px;display:block"></i><p>Nenhum alerta ativo no momento</p></div>';
            return;
        }

        this.alertsList.innerHTML = alerts.map(alert => this.createAlertHTML(alert)).join('');

        document.querySelectorAll('.cor-alert-item').forEach((item, index) => {
            item.addEventListener('click', () => this.focusAlert(alerts[index]));
        });
    }

    createAlertHTML(alert) {
        const priorityColors = {
            muito_alta: 'alta',
            alta: 'alta',
            media: 'media',
            baixa: 'baixa'
        };

        const priorityClass = priorityColors[alert.priority] || 'media';
        
        const statusBadges = alert.status === 'confirmado' 
            ? '<span class="cor-status-badge confirmado"><i class="bi bi-check-circle-fill"></i> Confirmado</span>'
            : '<span class="cor-status-badge apurando"><i class="bi bi-search"></i> Apurando</span>';

        return '<div class="cor-alert-item priority-' + priorityClass + '"><div class="cor-alert-item-header"><div class="cor-alert-icon ' + priorityClass + '"><i class="' + alert.icon + '"></i></div><div class="cor-alert-content"><span class="cor-alert-type">' + alert.priority.toUpperCase() + '</span><div class="cor-alert-title">' + alert.title + '</div><div class="cor-alert-description">' + alert.description + '</div><div class="cor-alert-time">' + alert.time + '</div></div></div><div class="cor-alert-footer"><div class="cor-alert-status">' + statusBadges + '</div><div class="cor-alert-actions"><button class="cor-action-btn" title="Localizar no mapa"><i class="bi bi-geo-alt"></i></button><button class="cor-action-btn" title="Ver estatísticas"><i class="bi bi-graph-up"></i></button><button class="cor-action-btn" title="Configurações"><i class="bi bi-gear"></i></button></div></div></div>';
    }

    focusAlert(alert) {
        if (typeof map !== 'undefined' && alert.lat && alert.lng) {
            map.setView([alert.lat, alert.lng], 15, {
                animate: true,
                duration: 1
            });
        }
    }

    updateBadge(count) {
        this.alertsBadge.textContent = count;
        if (count === 0) {
            this.alertsBadge.style.display = 'none';
        } else {
            this.alertsBadge.style.display = 'inline-block';
        }
    }

    formatTime(dateString) {
        if (!dateString) return 'Agora';
        
        const date = new Date(dateString);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);

        if (diff < 60) return 'Agora';
        if (diff < 3600) return Math.floor(diff / 60) + 'min atras';
        if (diff < 86400) return Math.floor(diff / 3600) + 'h atras';
        
        return date.toLocaleTimeString('pt-BR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.alertsManager = new AlertsManager();
    });
} else {
    window.alertsManager = new AlertsManager();
}

console.log('cor_alerts.js carregado');