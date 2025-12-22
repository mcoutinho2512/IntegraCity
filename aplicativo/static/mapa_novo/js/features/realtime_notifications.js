/**
 * Real-time Notifications System
 * SISCOR - Sistema de Notificações em Tempo Real
 */

const SISCORNotifications = (function() {
    'use strict';

    // Configurações
    const CONFIG = {
        pollInterval: 30000,           // 30 segundos
        maxNotifications: 50,          // Máximo de notificações em memória
        soundEnabled: true,
        desktopEnabled: true,
        storageKey: 'siscor_notifications',
        endpoints: {
            alertas: '/siscor/api/alertas/',
            ocorrencias: '/siscor/api/ocorrencias/hoje/',
            estagio: '/siscor/api/estagio-atual/'
        }
    };

    // Estado
    let notifications = [];
    let unreadCount = 0;
    let pollTimer = null;
    let lastCheck = {};
    let panel = null;
    let isOpen = false;

    // Sons
    const sounds = {
        alert: null,
        critical: null,
        info: null
    };

    /**
     * Inicializar sistema
     */
    function init() {
        console.log('🔔 Inicializando sistema de notificações...');

        // Carregar notificações salvas
        loadFromStorage();

        // Criar painel de notificações
        createPanel();

        // Configurar event listeners
        setupEventListeners();

        // Pedir permissão para notificações desktop
        requestDesktopPermission();

        // Iniciar polling
        startPolling();

        // Atualizar contador
        updateBadge();

        console.log('✅ Sistema de notificações inicializado');
    }

    /**
     * Criar painel de notificações
     */
    function createPanel() {
        // Remover painel existente se houver
        const existing = document.getElementById('notifications-panel-new');
        if (existing) existing.remove();

        panel = document.createElement('div');
        panel.id = 'notifications-panel-new';
        panel.className = 'notifications-panel';
        panel.innerHTML = `
            <div class="notifications-header">
                <h3><i class="bi bi-bell-fill"></i> Notificações</h3>
                <div class="notifications-actions">
                    <button class="btn-icon" id="mark-all-read" title="Marcar todas como lidas">
                        <i class="bi bi-check-all"></i>
                    </button>
                    <button class="btn-icon" id="clear-notifications" title="Limpar todas">
                        <i class="bi bi-trash"></i>
                    </button>
                    <button class="btn-icon" id="close-notifications" title="Fechar">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>
            </div>

            <div class="notifications-filter">
                <button class="filter-btn active" data-filter="all">Todas</button>
                <button class="filter-btn" data-filter="critical">Críticas</button>
                <button class="filter-btn" data-filter="alert">Alertas</button>
                <button class="filter-btn" data-filter="info">Info</button>
            </div>

            <div class="notifications-list" id="notifications-list">
                <div class="notifications-empty">
                    <i class="bi bi-bell-slash"></i>
                    <p>Nenhuma notificação</p>
                </div>
            </div>

            <div class="notifications-footer">
                <label class="toggle-option">
                    <input type="checkbox" id="sound-toggle" ${CONFIG.soundEnabled ? 'checked' : ''}>
                    <span><i class="bi bi-volume-up"></i> Som</span>
                </label>
                <label class="toggle-option">
                    <input type="checkbox" id="desktop-toggle" ${CONFIG.desktopEnabled ? 'checked' : ''}>
                    <span><i class="bi bi-window"></i> Desktop</span>
                </label>
            </div>
        `;

        // Adicionar estilos inline para o painel
        panel.style.cssText = `
            position: fixed;
            top: 60px;
            right: 16px;
            width: 380px;
            max-height: 70vh;
            background: #1e293b;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
            z-index: 2500;
            display: flex;
            flex-direction: column;
            transform: translateY(-10px);
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            border: 1px solid #334155;
        `;

        document.body.appendChild(panel);
    }

    /**
     * Configurar event listeners
     */
    function setupEventListeners() {
        // Toggle do painel
        const toggleBtn = document.getElementById('notifications-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', togglePanel);
        }

        // Botões do painel
        document.getElementById('close-notifications')?.addEventListener('click', closePanel);
        document.getElementById('mark-all-read')?.addEventListener('click', markAllAsRead);
        document.getElementById('clear-notifications')?.addEventListener('click', clearAll);

        // Filtros
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                renderNotifications(e.target.dataset.filter);
            });
        });

        // Toggles de configuração
        document.getElementById('sound-toggle')?.addEventListener('change', (e) => {
            CONFIG.soundEnabled = e.target.checked;
            saveSettings();
        });

        document.getElementById('desktop-toggle')?.addEventListener('change', (e) => {
            CONFIG.desktopEnabled = e.target.checked;
            saveSettings();
        });

        // Fechar ao clicar fora
        document.addEventListener('click', (e) => {
            if (isOpen && panel && !panel.contains(e.target) &&
                !e.target.closest('#notifications-toggle')) {
                closePanel();
            }
        });
    }

    /**
     * Toggle do painel
     */
    function togglePanel() {
        isOpen = !isOpen;
        if (panel) {
            panel.style.opacity = isOpen ? '1' : '0';
            panel.style.visibility = isOpen ? 'visible' : 'hidden';
            panel.style.transform = isOpen ? 'translateY(0)' : 'translateY(-10px)';
        }
        if (isOpen) {
            renderNotifications('all');
        }
    }

    /**
     * Fechar painel
     */
    function closePanel() {
        isOpen = false;
        if (panel) {
            panel.style.opacity = '0';
            panel.style.visibility = 'hidden';
            panel.style.transform = 'translateY(-10px)';
        }
    }

    /**
     * Iniciar polling
     */
    function startPolling() {
        // Primeira verificação
        checkForNewNotifications();

        // Polling periódico
        pollTimer = setInterval(checkForNewNotifications, CONFIG.pollInterval);
    }

    /**
     * Parar polling
     */
    function stopPolling() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    /**
     * Verificar novas notificações
     */
    async function checkForNewNotifications() {
        try {
            // Verificar estágio
            const estagioResponse = await fetch(CONFIG.endpoints.estagio);
            if (estagioResponse.ok) {
                const estagioData = await estagioResponse.json();
                processEstagioChange(estagioData);
            }

            // Verificar alertas
            const alertasResponse = await fetch(CONFIG.endpoints.alertas);
            if (alertasResponse.ok) {
                const alertasData = await alertasResponse.json();
                processAlertas(alertasData);
            }

            // Verificar ocorrências
            const ocorrenciasResponse = await fetch(CONFIG.endpoints.ocorrencias);
            if (ocorrenciasResponse.ok) {
                const ocorrenciasData = await ocorrenciasResponse.json();
                processOcorrencias(ocorrenciasData);
            }

        } catch (error) {
            console.warn('Erro ao verificar notificações:', error);
        }
    }

    /**
     * Processar mudança de estágio
     */
    function processEstagioChange(data) {
        if (!data.success || !data.data) return;

        const estagio = data.data;
        const lastEstagio = lastCheck.estagio;

        if (lastEstagio && lastEstagio.nivel !== estagio.nivel) {
            // Houve mudança de estágio
            addNotification({
                id: `estagio-${Date.now()}`,
                type: estagio.nivel >= 3 ? 'critical' : 'alert',
                title: `Estágio alterado para ${estagio.nome}`,
                message: estagio.descricao || 'Nível operacional atualizado',
                icon: 'bi-exclamation-triangle-fill',
                color: estagio.cor,
                timestamp: Date.now()
            });
        }

        lastCheck.estagio = estagio;
    }

    /**
     * Processar alertas
     */
    function processAlertas(data) {
        if (!data.success || !data.data) return;

        const alertas = Array.isArray(data.data) ? data.data : [data.data];
        const lastIds = lastCheck.alertas || [];

        alertas.forEach(alerta => {
            if (!lastIds.includes(alerta.id)) {
                addNotification({
                    id: `alerta-${alerta.id}`,
                    type: alerta.tipo === 'critico' ? 'critical' : 'alert',
                    title: alerta.titulo || 'Novo Alerta',
                    message: alerta.mensagem || alerta.descricao,
                    icon: 'bi-exclamation-circle-fill',
                    timestamp: Date.now()
                });
            }
        });

        lastCheck.alertas = alertas.map(a => a.id);
    }

    /**
     * Processar ocorrências
     */
    function processOcorrencias(data) {
        if (!data.success || !data.data) return;

        const ocorrencias = Array.isArray(data.data) ? data.data : [data.data];
        const lastIds = lastCheck.ocorrencias || [];

        ocorrencias.slice(0, 5).forEach(ocorrencia => {
            if (!lastIds.includes(ocorrencia.id)) {
                addNotification({
                    id: `ocorrencia-${ocorrencia.id}`,
                    type: 'info',
                    title: ocorrencia.tipo || 'Nova Ocorrência',
                    message: ocorrencia.endereco || ocorrencia.descricao,
                    icon: 'bi-geo-alt-fill',
                    timestamp: Date.now()
                });
            }
        });

        lastCheck.ocorrencias = ocorrencias.map(o => o.id);
    }

    /**
     * Adicionar notificação
     */
    function addNotification(notification) {
        // Evitar duplicatas
        if (notifications.some(n => n.id === notification.id)) {
            return;
        }

        notification.read = false;
        notifications.unshift(notification);

        // Limitar tamanho
        if (notifications.length > CONFIG.maxNotifications) {
            notifications.pop();
        }

        unreadCount++;
        updateBadge();
        saveToStorage();

        // Mostrar desktop notification
        if (CONFIG.desktopEnabled && Notification.permission === 'granted') {
            showDesktopNotification(notification);
        }

        // Tocar som
        if (CONFIG.soundEnabled) {
            playSound(notification.type);
        }

        // Atualizar lista se painel estiver aberto
        if (isOpen) {
            renderNotifications();
        }

        // Mostrar toast
        showToast(notification);
    }

    /**
     * Renderizar lista de notificações
     */
    function renderNotifications(filter = 'all') {
        const list = document.getElementById('notifications-list');
        if (!list) return;

        const filtered = filter === 'all'
            ? notifications
            : notifications.filter(n => n.type === filter);

        if (filtered.length === 0) {
            list.innerHTML = `
                <div class="notifications-empty">
                    <i class="bi bi-bell-slash"></i>
                    <p>Nenhuma notificação</p>
                </div>
            `;
            return;
        }

        list.innerHTML = filtered.map(n => `
            <div class="notification-item ${n.read ? '' : 'unread'}" data-id="${n.id}">
                <div class="notification-icon ${n.type}" style="${n.color ? 'background:' + n.color : ''}">
                    <i class="bi ${n.icon || 'bi-bell'}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${n.title}</div>
                    <div class="notification-message">${n.message || ''}</div>
                    <div class="notification-time">${formatTime(n.timestamp)}</div>
                </div>
                <button class="notification-dismiss" data-id="${n.id}">
                    <i class="bi bi-x"></i>
                </button>
            </div>
        `).join('');

        // Event listeners para itens
        list.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => markAsRead(item.dataset.id));
        });

        list.querySelectorAll('.notification-dismiss').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                removeNotification(btn.dataset.id);
            });
        });
    }

    /**
     * Formatar tempo
     */
    function formatTime(timestamp) {
        const diff = Date.now() - timestamp;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);

        if (minutes < 1) return 'Agora';
        if (minutes < 60) return `${minutes}m atrás`;
        if (hours < 24) return `${hours}h atrás`;
        return new Date(timestamp).toLocaleDateString('pt-BR');
    }

    /**
     * Marcar como lida
     */
    function markAsRead(id) {
        const notification = notifications.find(n => n.id === id);
        if (notification && !notification.read) {
            notification.read = true;
            unreadCount = Math.max(0, unreadCount - 1);
            updateBadge();
            saveToStorage();
            renderNotifications();
        }
    }

    /**
     * Marcar todas como lidas
     */
    function markAllAsRead() {
        notifications.forEach(n => n.read = true);
        unreadCount = 0;
        updateBadge();
        saveToStorage();
        renderNotifications();
    }

    /**
     * Remover notificação
     */
    function removeNotification(id) {
        const index = notifications.findIndex(n => n.id === id);
        if (index > -1) {
            if (!notifications[index].read) {
                unreadCount = Math.max(0, unreadCount - 1);
            }
            notifications.splice(index, 1);
            updateBadge();
            saveToStorage();
            renderNotifications();
        }
    }

    /**
     * Limpar todas
     */
    function clearAll() {
        notifications = [];
        unreadCount = 0;
        updateBadge();
        saveToStorage();
        renderNotifications();
    }

    /**
     * Atualizar badge
     */
    function updateBadge() {
        const badge = document.getElementById('notification-count');
        if (badge) {
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            badge.style.display = unreadCount > 0 ? 'flex' : 'none';
        }
    }

    /**
     * Mostrar toast
     */
    function showToast(notification) {
        const toast = document.createElement('div');
        toast.className = `cor-toast cor-toast-${notification.type}`;
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="bi ${notification.icon || 'bi-bell'}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-title">${notification.title}</div>
                <div class="toast-message">${notification.message || ''}</div>
            </div>
            <button class="toast-close"><i class="bi bi-x"></i></button>
        `;

        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #1e293b;
            padding: 16px;
            border-radius: 12px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
            max-width: 360px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            border-left: 4px solid ${notification.type === 'critical' ? '#ef4444' : notification.type === 'alert' ? '#f59e0b' : '#3b82f6'};
            z-index: 3000;
            animation: slideInRight 0.3s ease;
        `;

        document.body.appendChild(toast);

        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.remove();
        });

        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    /**
     * Mostrar desktop notification
     */
    function showDesktopNotification(notification) {
        if (Notification.permission === 'granted') {
            new Notification(notification.title, {
                body: notification.message,
                icon: '/static/images/siscor-icon-192.png',
                tag: notification.id,
                requireInteraction: notification.type === 'critical'
            });
        }
    }

    /**
     * Pedir permissão desktop
     */
    function requestDesktopPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }

    /**
     * Tocar som
     */
    function playSound(type) {
        // Implementação simples com Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = type === 'critical' ? 880 : type === 'alert' ? 660 : 440;
            oscillator.type = 'sine';

            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (e) {
            // Silenciar erros de áudio
        }
    }

    /**
     * Salvar em storage
     */
    function saveToStorage() {
        try {
            localStorage.setItem(CONFIG.storageKey, JSON.stringify({
                notifications: notifications.slice(0, 20),
                unreadCount
            }));
        } catch (e) {
            console.warn('Erro ao salvar notificações:', e);
        }
    }

    /**
     * Carregar do storage
     */
    function loadFromStorage() {
        try {
            const stored = localStorage.getItem(CONFIG.storageKey);
            if (stored) {
                const data = JSON.parse(stored);
                notifications = data.notifications || [];
                unreadCount = data.unreadCount || 0;
            }
        } catch (e) {
            console.warn('Erro ao carregar notificações:', e);
        }
    }

    /**
     * Salvar configurações
     */
    function saveSettings() {
        localStorage.setItem('siscor_notif_settings', JSON.stringify({
            soundEnabled: CONFIG.soundEnabled,
            desktopEnabled: CONFIG.desktopEnabled
        }));
    }

    // Inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // API Pública
    return {
        add: addNotification,
        markAsRead,
        markAllAsRead,
        clear: clearAll,
        getUnreadCount: () => unreadCount,
        toggle: togglePanel,
        startPolling,
        stopPolling
    };
})();

// Adicionar estilos de animação
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    .notification-item {
        display: flex;
        padding: 12px;
        gap: 12px;
        border-bottom: 1px solid #334155;
        cursor: pointer;
        transition: background 0.2s;
    }
    .notification-item:hover {
        background: rgba(59, 130, 246, 0.1);
    }
    .notification-item.unread {
        background: rgba(59, 130, 246, 0.05);
    }
    .notification-icon {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .notification-icon.critical { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
    .notification-icon.alert { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
    .notification-icon.info { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
    .notification-content { flex: 1; min-width: 0; }
    .notification-title { font-weight: 600; color: #f1f5f9; font-size: 14px; }
    .notification-message { color: #94a3b8; font-size: 13px; margin-top: 2px; }
    .notification-time { color: #64748b; font-size: 11px; margin-top: 4px; }
    .notification-dismiss {
        background: transparent;
        border: none;
        color: #64748b;
        cursor: pointer;
        padding: 4px;
    }
    .notification-dismiss:hover { color: #ef4444; }
    .notifications-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
        border-bottom: 1px solid #334155;
    }
    .notifications-header h3 {
        font-size: 16px;
        color: #f1f5f9;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .notifications-actions { display: flex; gap: 8px; }
    .notifications-filter {
        display: flex;
        padding: 8px;
        gap: 8px;
        border-bottom: 1px solid #334155;
    }
    .filter-btn {
        flex: 1;
        padding: 6px 12px;
        background: transparent;
        border: 1px solid #334155;
        border-radius: 6px;
        color: #94a3b8;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .filter-btn:hover, .filter-btn.active {
        background: #3b82f6;
        border-color: #3b82f6;
        color: white;
    }
    .notifications-list {
        flex: 1;
        overflow-y: auto;
        max-height: 400px;
    }
    .notifications-empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
        color: #64748b;
    }
    .notifications-empty i { font-size: 48px; margin-bottom: 12px; }
    .notifications-footer {
        display: flex;
        justify-content: space-around;
        padding: 12px;
        border-top: 1px solid #334155;
    }
    .toggle-option {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #94a3b8;
        font-size: 12px;
        cursor: pointer;
    }
    .btn-icon {
        background: transparent;
        border: none;
        color: #94a3b8;
        cursor: pointer;
        padding: 8px;
        border-radius: 6px;
    }
    .btn-icon:hover { background: rgba(255,255,255,0.1); color: #f1f5f9; }
`;
document.head.appendChild(style);

window.SISCORNotifications = SISCORNotifications;
console.log('✅ realtime_notifications.js carregado');
