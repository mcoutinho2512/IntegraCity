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

    // Simular atualização (substituir por chamada AJAX real)
    setTimeout(() => {
        hideLoading();
        showToast('Dados atualizados com sucesso', 'success');
    }, 1500);
}

// ============================================
// 8. SHOW NOTIFICATIONS
// ============================================
function showNotifications() {
    showToast('Central de notificações', 'info');
    // Implementar abertura do painel de notificações
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

    // Toast de inicialização
    setTimeout(() => {
        showToast('Sistema inicializado', 'success');
    }, 500);

    // Log de inicialização
    console.log('IntegraCity High-Tech Interface initialized');
    console.log('Keyboard shortcuts: F=Fullscreen, S=Sidebar, R=Refresh, ESC=Close');
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
    showSettings,
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
