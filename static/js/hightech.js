/* ============================================
   INTEGRACITY - HIGH-TECH JAVASCRIPT
   Funcionalidades do Command Center
   ============================================ */

console.log('🚀 hightech.js carregando...');

// ============================================
// 1. SISTEMA DE TOASTS (NOTIFICAÇÕES)
// ============================================
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon;
    switch (type) {
        case 'success':
            icon = 'fa-check-circle';
            break;
        case 'error':
            icon = 'fa-times-circle';
            break;
        case 'warning':
            icon = 'fa-exclamation-triangle';
            break;
        default:
            icon = 'fa-info-circle';
    }

    toast.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    // Auto-remove após 4 segundos
    setTimeout(() => {
        toast.style.animation = 'slideDown 0.3s ease forwards';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 4000);
}

// ============================================
// 2. TOGGLE SIDEBAR
// ============================================
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('toggleBtn');
    const mapWrapper = document.getElementById('mapWrapper');

    if (!sidebar || !toggleBtn || !mapWrapper) return;

    sidebar.classList.toggle('collapsed');
    toggleBtn.classList.toggle('collapsed');
    mapWrapper.classList.toggle('expanded');

    // Redimensionar mapa após transição
    setTimeout(() => {
        if (typeof map !== 'undefined' && map.invalidateSize) {
            map.invalidateSize();
        }
    }, 350);

    // Mostrar toast informativo
    if (sidebar.classList.contains('collapsed')) {
        showToast('Painel recolhido', 'info');
    } else {
        showToast('Painel expandido', 'info');
    }
}

// Toggle sidebar para mobile (fullscreen)
function toggleMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('toggleBtn');
    const menuBtn = document.querySelector('.mobile-menu-btn');

    if (!sidebar) return;

    sidebar.classList.toggle('mobile-open');

    if (toggleBtn) {
        toggleBtn.classList.toggle('mobile-open');
    }

    // Mudar ícone do botão hamburger
    if (menuBtn) {
        const icon = menuBtn.querySelector('i');
        if (sidebar.classList.contains('mobile-open')) {
            icon.className = 'fas fa-times';
        } else {
            icon.className = 'fas fa-bars';
        }
    }

    // Redimensionar mapa após transição
    setTimeout(() => {
        if (typeof map !== 'undefined' && map.invalidateSize) {
            map.invalidateSize();
        }
    }, 350);
}

// ============================================
// 3. LOADING OVERLAY
// ============================================
function showLoading(message = 'PROCESSANDO...') {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        const textEl = overlay.querySelector('.loading-text');
        if (textEl) {
            textEl.textContent = message;
        }
        overlay.classList.add('active');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// ============================================
// 4. SWITCH MAP LAYER
// ============================================
function switchLayer(btn, layerName) {
    // Atualizar botões
    document.querySelectorAll('.layer-btn').forEach(b => {
        b.classList.remove('active');
    });
    if (btn) {
        btn.classList.add('active');
    }

    // Trocar camada do mapa (se Leaflet estiver disponível)
    if (typeof map !== 'undefined' && typeof layers !== 'undefined') {
        Object.values(layers).forEach(layer => {
            if (map.hasLayer(layer)) {
                map.removeLayer(layer);
            }
        });
        if (layers[layerName]) {
            layers[layerName].addTo(map);
        }
    }

    showToast(`Camada: ${layerName.toUpperCase()}`, 'success');
}

// ============================================
// 5. TOGGLE FULLSCREEN
// ============================================
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().then(() => {
            showToast('Modo tela cheia ativado', 'success');
        }).catch(err => {
            showToast('Erro ao ativar tela cheia', 'error');
        });
    } else {
        document.exitFullscreen().then(() => {
            showToast('Modo tela cheia desativado', 'info');
        });
    }
}

// ============================================
// 6. SHOW DETAIL (Click nos cards)
// ============================================
function showDetail(title, data = null) {
    showToast(`Abrindo detalhes: ${title}`, 'info');

    // Aqui você pode implementar a lógica para abrir um modal
    // ou navegar para uma página de detalhes
    console.log('Show detail:', title, data);
}

// ============================================
// 7. REFRESH DATA
// ============================================
function refreshData() {
    showLoading('ATUALIZANDO DADOS...');

    // Array of refresh promises
    const refreshPromises = [];

    // Refresh ocorrencias layer if function exists
    if (typeof carregarOcorrencias === 'function') {
        refreshPromises.push(
            Promise.resolve().then(() => {
                carregarOcorrencias();
                return 'ocorrencias';
            }).catch(e => console.log('Error refreshing ocorrencias:', e))
        );
    }

    // Refresh cameras layer if function exists
    if (typeof carregarCameras === 'function') {
        refreshPromises.push(
            Promise.resolve().then(() => {
                carregarCameras();
                return 'cameras';
            }).catch(e => console.log('Error refreshing cameras:', e))
        );
    }

    // Refresh waze layer if function exists
    if (typeof carregarWaze === 'function') {
        refreshPromises.push(
            Promise.resolve().then(() => {
                carregarWaze();
                return 'waze';
            }).catch(e => console.log('Error refreshing waze:', e))
        );
    }

    // Refresh areas if function exists
    if (typeof carregarAreasExistentes === 'function') {
        refreshPromises.push(
            Promise.resolve().then(() => {
                carregarAreasExistentes();
                return 'areas';
            }).catch(e => console.log('Error refreshing areas:', e))
        );
    }

    // Refresh escolas if function exists
    if (typeof carregarEscolas === 'function') {
        refreshPromises.push(
            Promise.resolve().then(() => {
                carregarEscolas();
                return 'escolas';
            }).catch(e => console.log('Error refreshing escolas:', e))
        );
    }

    // Refresh sirenes if function exists
    if (typeof carregarSirenes === 'function') {
        refreshPromises.push(
            Promise.resolve().then(() => {
                carregarSirenes();
                return 'sirenes';
            }).catch(e => console.log('Error refreshing sirenes:', e))
        );
    }

    // Refresh bolsoes if function exists
    if (typeof carregarBolsoes === 'function') {
        refreshPromises.push(
            Promise.resolve().then(() => {
                carregarBolsoes();
                return 'bolsoes';
            }).catch(e => console.log('Error refreshing bolsoes:', e))
        );
    }

    // If no specific refresh functions, simulate update
    if (refreshPromises.length === 0) {
        setTimeout(() => {
            hideLoading();
            showToast('Dados atualizados', 'success');
            addSystemNotification('Dados Atualizados', 'Refresh manual realizado', 'success', 'fa-sync-alt');
        }, 1000);
        return;
    }

    // Wait for all refreshes
    Promise.all(refreshPromises)
        .then(results => {
            hideLoading();
            const refreshedLayers = results.filter(r => r).length;
            showToast(`${refreshedLayers} camadas atualizadas`, 'success');
            addSystemNotification('Dados Atualizados', `${refreshedLayers} camadas atualizadas com sucesso`, 'success', 'fa-sync-alt');
        })
        .catch(error => {
            hideLoading();
            showToast('Erro ao atualizar dados', 'error');
            console.error('Refresh error:', error);
        });
}

// ============================================
// 8. SHOW NOTIFICATIONS
// ============================================

// Notifications storage
let notificationsData = [];
let currentNotificationFilter = 'todas';

function showNotifications() {
    const modal = document.getElementById('notificationsModal');
    if (modal) {
        modal.classList.add('active');
        loadNotifications();
    }
}

function closeNotifications() {
    const modal = document.getElementById('notificationsModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

function switchNotificationsTab(tabName) {
    currentNotificationFilter = tabName;

    // Update tab buttons
    document.querySelectorAll('.notifications-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Re-render notifications with filter
    renderNotifications();
}

function loadNotifications() {
    const list = document.getElementById('notificationsList');
    if (list) {
        // Show loading
        list.innerHTML = '<div class="notifications-loading"><i class="fas fa-spinner fa-spin"></i> Carregando notificacoes...</div>';
    }

    console.log('📢 loadNotifications() chamado');

    // Load notifications from multiple sources
    return Promise.all([
        loadOcorrenciasNotifications(),
        loadSystemNotifications()
    ]).then(([ocorrencias, sistema]) => {
        console.log('📢 Ocorrencias carregadas:', ocorrencias.length, ocorrencias);
        console.log('📢 Sistema carregadas:', sistema.length);

        notificationsData = [...ocorrencias, ...sistema];
        console.log('📢 Total notificationsData:', notificationsData.length);

        // Sort by date (newest first)
        notificationsData.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        if (list) {
            renderNotifications();
        }
        updateNotificationBadge();
    }).catch(error => {
        console.error('Error loading notifications:', error);
        if (list) {
            list.innerHTML = '<div class="notification-empty"><i class="fas fa-exclamation-circle"></i><p>Erro ao carregar notificacoes</p></div>';
        }
    });
}

function loadOcorrenciasNotifications() {
    return fetch('/integracity/api/ocorrencias/mapa/', {
        credentials: 'same-origin'
    })
        .then(response => {
            if (!response.ok) {
                console.log('Ocorrencias API response:', response.status);
                return { data: [] };
            }
            return response.json();
        })
        .then(data => {
            console.log('Ocorrencias API data:', data);
            const ocorrencias = data.data || data.ocorrencias || [];

            // Get last 10 recent occurrences
            return ocorrencias.slice(0, 10).map(oc => ({
                id: oc.id,
                type: 'ocorrencias',
                title: oc.titulo || oc.protocolo || 'Nova Ocorrencia',
                description: oc.categoria || oc.status_display || oc.status || 'Ocorrencia registrada',
                timestamp: oc.data_abertura || oc.criado_em || new Date().toISOString(),
                read: false,
                icon: 'fa-exclamation-circle',
                iconClass: 'ocorrencias',
                latitude: oc.latitude,
                longitude: oc.longitude
            }));
        })
        .catch(error => {
            console.log('Ocorrencias API error:', error);
            return [];
        });
}

function loadSystemNotifications() {
    // Get system notifications from localStorage or generate default ones
    const savedNotifications = localStorage.getItem('integracity_system_notifications');
    let systemNotifications = [];

    if (savedNotifications) {
        try {
            systemNotifications = JSON.parse(savedNotifications);
        } catch (e) {
            systemNotifications = [];
        }
    }

    // Add some default system notifications if empty
    if (systemNotifications.length === 0) {
        const now = new Date();
        systemNotifications = [
            {
                id: 'sys_1',
                type: 'sistema',
                title: 'Sistema Inicializado',
                description: 'IntegraCity Command Center operacional',
                timestamp: now.toISOString(),
                read: true,
                icon: 'fa-check-circle',
                iconClass: 'success'
            },
            {
                id: 'sys_2',
                type: 'sistema',
                title: 'Configuracoes Carregadas',
                description: 'Preferencias do usuario aplicadas',
                timestamp: new Date(now - 60000).toISOString(),
                read: true,
                icon: 'fa-cog',
                iconClass: 'sistema'
            }
        ];
    }

    return Promise.resolve(systemNotifications);
}

function renderNotifications() {
    const list = document.getElementById('notificationsList');
    if (!list) return;

    console.log('📢 renderNotifications() - filtro:', currentNotificationFilter);
    console.log('📢 Total em notificationsData:', notificationsData.length);
    console.log('📢 Tipos disponíveis:', notificationsData.map(n => n.type));

    // Filter notifications based on current tab
    let filtered = notificationsData;
    if (currentNotificationFilter !== 'todas') {
        filtered = notificationsData.filter(n => n.type === currentNotificationFilter);
    }

    console.log('📢 Após filtro:', filtered.length);

    if (filtered.length === 0) {
        list.innerHTML = `
            <div class="notification-empty">
                <i class="fas fa-bell-slash"></i>
                <p>Nenhuma notificacao ${currentNotificationFilter !== 'todas' ? 'nesta categoria' : ''}</p>
            </div>
        `;
        return;
    }

    list.innerHTML = filtered.map(notification => {
        const timeAgo = getTimeAgo(notification.timestamp);
        return `
            <div class="notification-item ${notification.read ? '' : 'unread'}"
                 onclick="handleNotificationClick('${notification.id}', ${notification.latitude || 'null'}, ${notification.longitude || 'null'})">
                <div class="notification-icon ${notification.iconClass}">
                    <i class="fas ${notification.icon}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-description">${notification.description}</div>
                    <div class="notification-time">${timeAgo}</div>
                </div>
            </div>
        `;
    }).join('');
}

function handleNotificationClick(id, lat, lng) {
    // Mark as read
    const notification = notificationsData.find(n => n.id === id);
    if (notification) {
        notification.read = true;
    }

    // Close modal
    closeNotifications();

    // If has coordinates, navigate to location
    if (lat && lng && typeof map !== 'undefined') {
        map.setView([lat, lng], 16);
        showToast('Navegando para a ocorrencia', 'info');
    }

    // Update notification badge
    updateNotificationBadge();
}

function updateNotificationBadge() {
    const unreadCount = notificationsData.filter(n => !n.read).length;
    const badge = document.querySelector('.notification-badge');

    if (badge) {
        if (unreadCount > 0) {
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    }
}

function clearAllNotifications() {
    if (confirm('Tem certeza que deseja limpar todas as notificacoes?')) {
        notificationsData = [];
        localStorage.removeItem('integracity_system_notifications');
        renderNotifications();
        updateNotificationBadge();
        showToast('Notificacoes limpas', 'success');
    }
}

function markAllAsRead() {
    notificationsData.forEach(n => n.read = true);
    renderNotifications();
    updateNotificationBadge();
    showToast('Todas marcadas como lidas', 'success');
}

function addSystemNotification(title, description, iconClass = 'sistema', icon = 'fa-info-circle') {
    const notification = {
        id: 'sys_' + Date.now(),
        type: 'sistema',
        title: title,
        description: description,
        timestamp: new Date().toISOString(),
        read: false,
        icon: icon,
        iconClass: iconClass
    };

    // Add to current data
    notificationsData.unshift(notification);

    // Save to localStorage
    const systemNotifications = notificationsData.filter(n => n.type === 'sistema');
    localStorage.setItem('integracity_system_notifications', JSON.stringify(systemNotifications.slice(0, 50)));

    // Update badge
    updateNotificationBadge();

    return notification;
}

function getTimeAgo(timestamp) {
    const now = new Date();
    const date = new Date(timestamp);
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'Agora mesmo';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min atras`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} h atras`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} dias atras`;

    return date.toLocaleDateString('pt-BR');
}

// ============================================
// 9. SETTINGS MANAGEMENT
// ============================================

// Default settings
const defaultSettings = {
    // Map settings
    mapLat: -22.92,
    mapLng: -43.45,
    mapZoom: 11,
    layerOcorrencias: true,
    layerWaze: true,
    layerCameras: false,
    layerEscolas: false,
    layerSirenes: false,

    // Tour settings
    tourAutoStart: true,
    tourTimeOcorrencia: 6,
    tourTimeOriginal: 6,
    tourZoom: 16,

    // Notification settings
    soundEnabled: false,
    notifyOcorrencias: true,
    notifyWaze: true,
    notifyMeteo: false,
    notifyStatus: true,
    browserNotify: false,

    // Interface settings
    theme: 'dark',
    fontSize: 100,
    sidebarExpanded: false,
    animations: true
};

// Current settings
let appSettings = { ...defaultSettings };

// Load settings from localStorage
function loadSettings() {
    try {
        const saved = localStorage.getItem('integracity_settings');
        if (saved) {
            appSettings = { ...defaultSettings, ...JSON.parse(saved) };
        }
    } catch (e) {
        console.error('Error loading settings:', e);
        appSettings = { ...defaultSettings };
    }
    return appSettings;
}

// Save settings to localStorage
function saveSettingsToStorage() {
    try {
        localStorage.setItem('integracity_settings', JSON.stringify(appSettings));
    } catch (e) {
        console.error('Error saving settings:', e);
    }
}

// Open settings modal
function showSettings() {
    console.log('⚙️ showSettings() chamado');
    const modal = document.getElementById('settingsModal');
    console.log('⚙️ Modal encontrado:', modal);
    if (modal) {
        loadSettings();
        populateSettingsForm();
        modal.classList.add('active');
        console.log('⚙️ Modal ativado');
    } else {
        console.error('❌ Modal de configurações não encontrado!');
    }
}

// Show profile tab directly
function showProfile() {
    const modal = document.getElementById('settingsModal');
    if (modal) {
        loadSettings();
        populateSettingsForm();
        modal.classList.add('active');
        // Switch to profile tab
        switchSettingsTab('perfil');
    }
}

// Close settings modal
function closeSettings() {
    const modal = document.getElementById('settingsModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

// Switch settings tab
function switchSettingsTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.settings-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Update tab content
    document.querySelectorAll('.settings-tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabName}`);
    });
}

// Populate form with current settings
function populateSettingsForm() {
    // Map settings
    setInputValue('settingMapLat', appSettings.mapLat);
    setInputValue('settingMapLng', appSettings.mapLng);
    setInputValue('settingMapZoom', appSettings.mapZoom);
    setCheckbox('settingLayerOcorrencias', appSettings.layerOcorrencias);
    setCheckbox('settingLayerWaze', appSettings.layerWaze);
    setCheckbox('settingLayerCameras', appSettings.layerCameras);
    setCheckbox('settingLayerEscolas', appSettings.layerEscolas);
    setCheckbox('settingLayerSirenes', appSettings.layerSirenes);

    // Tour settings
    setCheckbox('settingTourAutoStart', appSettings.tourAutoStart);
    setSlider('settingTourTimeOcorrencia', appSettings.tourTimeOcorrencia, 'tourTimeOcorrenciaValue');
    setSlider('settingTourTimeOriginal', appSettings.tourTimeOriginal, 'tourTimeOriginalValue');
    setSlider('settingTourZoom', appSettings.tourZoom, 'tourZoomValue');

    // Notification settings
    setCheckbox('settingSoundEnabled', appSettings.soundEnabled);
    setCheckbox('settingNotifyOcorrencias', appSettings.notifyOcorrencias);
    setCheckbox('settingNotifyWaze', appSettings.notifyWaze);
    setCheckbox('settingNotifyMeteo', appSettings.notifyMeteo);
    setCheckbox('settingNotifyStatus', appSettings.notifyStatus);
    setCheckbox('settingBrowserNotify', appSettings.browserNotify);

    // Interface settings
    setRadio('theme', appSettings.theme);
    setSlider('settingFontSize', appSettings.fontSize, 'fontSizeValue');
    setCheckbox('settingSidebarExpanded', appSettings.sidebarExpanded);
    setCheckbox('settingAnimations', appSettings.animations);
}

// Helper functions
function setInputValue(id, value) {
    const el = document.getElementById(id);
    if (el) el.value = value;
}

function setCheckbox(id, checked) {
    const el = document.getElementById(id);
    if (el) el.checked = checked;
}

function setRadio(name, value) {
    const el = document.querySelector(`input[name="${name}"][value="${value}"]`);
    if (el) el.checked = true;
}

function setSlider(id, value, displayId) {
    const el = document.getElementById(id);
    const display = document.getElementById(displayId);
    if (el) {
        el.value = value;
        if (display) display.textContent = value;
    }
}

// Collect settings from form
function collectSettings() {
    return {
        // Map settings
        mapLat: parseFloat(document.getElementById('settingMapLat')?.value) || defaultSettings.mapLat,
        mapLng: parseFloat(document.getElementById('settingMapLng')?.value) || defaultSettings.mapLng,
        mapZoom: parseInt(document.getElementById('settingMapZoom')?.value) || defaultSettings.mapZoom,
        layerOcorrencias: document.getElementById('settingLayerOcorrencias')?.checked ?? true,
        layerWaze: document.getElementById('settingLayerWaze')?.checked ?? true,
        layerCameras: document.getElementById('settingLayerCameras')?.checked ?? false,
        layerEscolas: document.getElementById('settingLayerEscolas')?.checked ?? false,
        layerSirenes: document.getElementById('settingLayerSirenes')?.checked ?? false,

        // Tour settings
        tourAutoStart: document.getElementById('settingTourAutoStart')?.checked ?? true,
        tourTimeOcorrencia: parseInt(document.getElementById('settingTourTimeOcorrencia')?.value) || 6,
        tourTimeOriginal: parseInt(document.getElementById('settingTourTimeOriginal')?.value) || 6,
        tourZoom: parseInt(document.getElementById('settingTourZoom')?.value) || 16,

        // Notification settings
        soundEnabled: document.getElementById('settingSoundEnabled')?.checked ?? false,
        notifyOcorrencias: document.getElementById('settingNotifyOcorrencias')?.checked ?? true,
        notifyWaze: document.getElementById('settingNotifyWaze')?.checked ?? true,
        notifyMeteo: document.getElementById('settingNotifyMeteo')?.checked ?? false,
        notifyStatus: document.getElementById('settingNotifyStatus')?.checked ?? true,
        browserNotify: document.getElementById('settingBrowserNotify')?.checked ?? false,

        // Interface settings
        theme: document.querySelector('input[name="theme"]:checked')?.value || 'dark',
        fontSize: parseInt(document.getElementById('settingFontSize')?.value) || 100,
        sidebarExpanded: document.getElementById('settingSidebarExpanded')?.checked ?? false,
        animations: document.getElementById('settingAnimations')?.checked ?? true
    };
}

// Save settings
function saveSettings() {
    appSettings = collectSettings();
    saveSettingsToStorage();
    applySettings();
    closeSettings();
    showToast('Configuracoes salvas com sucesso!', 'success');
}

// Reset settings to default
function resetSettings() {
    if (confirm('Tem certeza que deseja restaurar as configuracoes padrao?')) {
        appSettings = { ...defaultSettings };
        populateSettingsForm();
        showToast('Configuracoes restauradas', 'info');
    }
}

// Apply settings to the interface
function applySettings() {
    // Apply font size
    document.documentElement.style.fontSize = `${appSettings.fontSize}%`;

    // Apply theme
    document.body.classList.toggle('light-theme', appSettings.theme === 'light');

    // Apply animations
    document.body.classList.toggle('no-animations', !appSettings.animations);

    // Update tour settings if available
    if (typeof window.TEMPO_EM_OCORRENCIA !== 'undefined') {
        window.TEMPO_EM_OCORRENCIA = appSettings.tourTimeOcorrencia * 1000;
    }
    if (typeof window.TEMPO_NA_POSICAO_ORIGINAL !== 'undefined') {
        window.TEMPO_NA_POSICAO_ORIGINAL = appSettings.tourTimeOriginal * 1000;
    }
    if (typeof window.ZOOM_OCORRENCIA !== 'undefined') {
        window.ZOOM_OCORRENCIA = appSettings.tourZoom;
    }
    if (typeof window.posicaoOriginal !== 'undefined') {
        window.posicaoOriginal = {
            lat: appSettings.mapLat,
            lng: appSettings.mapLng,
            zoom: appSettings.mapZoom
        };
    }

    // Dispatch custom event for other modules
    window.dispatchEvent(new CustomEvent('settingsChanged', { detail: appSettings }));
}

// Use current map position
function useCurrentMapPosition() {
    if (typeof map !== 'undefined') {
        const center = map.getCenter();
        const zoom = map.getZoom();
        document.getElementById('settingMapLat').value = center.lat.toFixed(4);
        document.getElementById('settingMapLng').value = center.lng.toFixed(4);
        document.getElementById('settingMapZoom').value = zoom;
        showToast('Posicao do mapa capturada', 'success');
    } else {
        showToast('Mapa nao disponivel', 'error');
    }
}

// Request browser notification permission
function requestNotificationPermission() {
    if ('Notification' in window) {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                document.getElementById('settingBrowserNotify').checked = true;
                showToast('Permissao de notificacoes concedida', 'success');
            } else {
                document.getElementById('settingBrowserNotify').checked = false;
                showToast('Permissao de notificacoes negada', 'warning');
            }
        });
    } else {
        showToast('Navegador nao suporta notificacoes', 'error');
    }
}

// Change password (placeholder - needs backend)
function changePassword() {
    const currentPass = document.getElementById('settingCurrentPassword')?.value;
    const newPass = document.getElementById('settingNewPassword')?.value;
    const confirmPass = document.getElementById('settingConfirmPassword')?.value;

    if (!currentPass || !newPass || !confirmPass) {
        showToast('Preencha todos os campos de senha', 'error');
        return;
    }

    if (newPass !== confirmPass) {
        showToast('As senhas nao coincidem', 'error');
        return;
    }

    if (newPass.length < 6) {
        showToast('A senha deve ter pelo menos 6 caracteres', 'error');
        return;
    }

    // TODO: Implement backend call
    showToast('Funcao de alteracao de senha em desenvolvimento', 'info');
}

// Initialize slider value display updates
function initSettingsSliders() {
    const sliders = [
        { id: 'settingTourTimeOcorrencia', displayId: 'tourTimeOcorrenciaValue' },
        { id: 'settingTourTimeOriginal', displayId: 'tourTimeOriginalValue' },
        { id: 'settingTourZoom', displayId: 'tourZoomValue' },
        { id: 'settingFontSize', displayId: 'fontSizeValue' }
    ];

    sliders.forEach(({ id, displayId }) => {
        const slider = document.getElementById(id);
        const display = document.getElementById(displayId);
        if (slider && display) {
            slider.addEventListener('input', () => {
                display.textContent = slider.value;
            });
        }
    });
}

// Get current settings (for other modules)
function getSettings() {
    return { ...appSettings };
}

// ============================================
// 10. ZOOM CONTROLS
// ============================================
function zoomIn() {
    if (typeof map !== 'undefined') {
        map.zoomIn();
    }
}

function zoomOut() {
    if (typeof map !== 'undefined') {
        map.zoomOut();
    }
}

function resetView() {
    if (typeof map !== 'undefined') {
        // Centro do Município do Rio de Janeiro
        map.setView([-22.92, -43.45], 11);
        showToast('Visualização resetada', 'info');
    }
}

// ============================================
// 11. LOCATE USER
// ============================================
function locateUser() {
    if (typeof map !== 'undefined' && navigator.geolocation) {
        showLoading('LOCALIZANDO...');
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                map.setView([latitude, longitude], 15);
                L.marker([latitude, longitude])
                    .addTo(map)
                    .bindPopup('Sua localização')
                    .openPopup();
                hideLoading();
                showToast('Localização encontrada', 'success');
            },
            (error) => {
                hideLoading();
                showToast('Erro ao obter localização', 'error');
            }
        );
    } else {
        showToast('Geolocalização não suportada', 'warning');
    }
}

// ============================================
// 12. TOGGLE MAP CONTROL
// ============================================
function toggleMapControl(btn, controlName) {
    btn.classList.toggle('active');

    const isActive = btn.classList.contains('active');
    showToast(`${controlName}: ${isActive ? 'Ativado' : 'Desativado'}`, 'info');

    // Implementar lógica específica para cada controle
    console.log('Toggle control:', controlName, isActive);
}

// ============================================
// 13. UPDATE CLOCK
// ============================================
function updateClock() {
    const clockElement = document.getElementById('systemClock');
    if (clockElement) {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        clockElement.textContent = `${hours}:${minutes}:${seconds}`;
    }
}

// ============================================
// 14. UPDATE DATE
// ============================================
function updateDate() {
    const dateElement = document.getElementById('systemDate');
    if (dateElement) {
        const now = new Date();
        const day = String(now.getDate()).padStart(2, '0');
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const year = now.getFullYear();
        dateElement.textContent = `${day}/${month}/${year}`;
    }
}

// ============================================
// 15. KEYBOARD SHORTCUTS
// ============================================
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Escape - Fechar modais/overlays
        if (e.key === 'Escape') {
            hideLoading();
            closeSettings();
            closeNotifications();
        }

        // F - Fullscreen (quando não estiver em input)
        if (e.key === 'f' && !e.target.matches('input, textarea')) {
            e.preventDefault();
            toggleFullscreen();
        }

        // S - Toggle Sidebar (não quando settings está aberta)
        if (e.key === 's' && !e.target.matches('input, textarea')) {
            const settingsModal = document.getElementById('settingsModal');
            if (!settingsModal || !settingsModal.classList.contains('active')) {
                e.preventDefault();
                toggleSidebar();
            }
        }

        // R - Refresh
        if (e.key === 'r' && !e.target.matches('input, textarea') && !e.ctrlKey) {
            e.preventDefault();
            refreshData();
        }

        // N - Notifications
        if (e.key === 'n' && !e.target.matches('input, textarea')) {
            const notificationsModal = document.getElementById('notificationsModal');
            if (!notificationsModal || !notificationsModal.classList.contains('active')) {
                e.preventDefault();
                showNotifications();
            }
        }
    });
}

// ============================================
// 16. CARD CLICK HANDLERS
// ============================================
function initCardHandlers() {
    document.querySelectorAll('.monitor-card').forEach(card => {
        card.addEventListener('click', function() {
            const title = this.querySelector('.card-title')?.textContent || 'Item';
            const value = this.querySelector('.card-value')?.textContent || '';
            showDetail(title, { value });
        });
    });
}

// ============================================
// 17. MOBILE MENU
// ============================================
function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('toggleBtn');

    if (sidebar && toggleBtn) {
        sidebar.classList.toggle('mobile-open');
        toggleBtn.classList.toggle('mobile-open');
    }
}

// ============================================
// 18. INITIALIZE
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    // Carregar e aplicar configurações salvas
    loadSettings();
    applySettings();

    // Inicializar sliders das configurações
    initSettingsSliders();

    // Inicializar relógio
    updateClock();
    updateDate();
    setInterval(updateClock, 1000);
    setInterval(updateDate, 60000);

    // Inicializar atalhos de teclado
    initKeyboardShortcuts();

    // Inicializar handlers dos cards
    initCardHandlers();

    // Fechar settings modal ao clicar fora
    const settingsModal = document.getElementById('settingsModal');
    if (settingsModal) {
        settingsModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeSettings();
            }
        });
    }

    // Fechar notifications modal ao clicar fora
    const notificationsModal = document.getElementById('notificationsModal');
    if (notificationsModal) {
        notificationsModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeNotifications();
            }
        });
    }

    // Inicializar badge de notificações
    setTimeout(() => {
        loadNotifications().catch(() => {});
    }, 2000);

    // Toast de inicialização
    setTimeout(() => {
        showToast('Sistema inicializado', 'success');
    }, 500);

    // Log de inicialização
    console.log('IntegraCity High-Tech Interface initialized');
    console.log('Keyboard shortcuts: F=Fullscreen, S=Sidebar, R=Refresh, N=Notifications, ESC=Close');
});

// ============================================
// 19. AJAX UTILITIES
// ============================================
function fetchData(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
    };

    return fetch(url, { ...defaultOptions, ...options })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            showToast(`Erro: ${error.message}`, 'error');
            throw error;
        });
}

// ============================================
// 20. WEBSOCKET CONNECTION (opcional)
// ============================================
function initWebSocket(url) {
    if (!url) return null;

    const ws = new WebSocket(url);

    ws.onopen = () => {
        console.log('WebSocket connected');
        showToast('Conexão em tempo real ativa', 'success');
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (e) {
            console.error('WebSocket message error:', e);
        }
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        showToast('Conexão perdida. Reconectando...', 'warning');
        // Auto-reconnect após 5 segundos
        setTimeout(() => initWebSocket(url), 5000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    return ws;
}

function handleWebSocketMessage(data) {
    // Implementar lógica de atualização em tempo real
    console.log('WebSocket message:', data);

    if (data.type === 'notification') {
        showToast(data.message, data.level || 'info');
    }
}

// ============================================
// 21. EXPORT FOR GLOBAL USE
// ============================================
window.IntegraCity = {
    showToast,
    toggleSidebar,
    toggleMobileSidebar,
    showLoading,
    hideLoading,
    switchLayer,
    toggleFullscreen,
    showDetail,
    refreshData,
    showNotifications,
    closeNotifications,
    switchNotificationsTab,
    loadNotifications,
    clearAllNotifications,
    markAllAsRead,
    addSystemNotification,
    updateNotificationBadge,
    showSettings,
    showProfile,
    closeSettings,
    switchSettingsTab,
    saveSettings,
    resetSettings,
    getSettings,
    loadSettings,
    applySettings,
    useCurrentMapPosition,
    requestNotificationPermission,
    changePassword,
    zoomIn,
    zoomOut,
    resetView,
    locateUser,
    fetchData,
    initWebSocket,
    toggleCard,
};

console.log('✅ hightech.js carregado! showSettings disponível:', typeof showSettings);

// ====================================
// TOGGLE CARD RETRÁTIL
// ====================================

function toggleCard(cardElement) {
    // Toggle expanded class no card clicado
    cardElement.classList.toggle('expanded');

    // OPCIONAL: Fechar outros cards ao abrir um novo
    // Descomente as linhas abaixo se quiser apenas 1 card aberto por vez
    /*
    const allCards = document.querySelectorAll('.compact-card');
    allCards.forEach(card => {
        if (card !== cardElement && card.classList.contains('expanded')) {
            card.classList.remove('expanded');
        }
    });
    */
}
