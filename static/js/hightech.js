/* ============================================
   INTEGRACITY - HIGH-TECH JAVASCRIPT
   Funcionalidades do Command Center
   ============================================ */

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
// 9. SHOW SETTINGS
// ============================================
function showSettings() {
    showToast('Configurações do sistema', 'info');
    // Implementar abertura das configurações
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
        const options = { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' };
        dateElement.textContent = now.toLocaleDateString('pt-BR', options).toUpperCase();
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
        }

        // F - Fullscreen (quando não estiver em input)
        if (e.key === 'f' && !e.target.matches('input, textarea')) {
            e.preventDefault();
            toggleFullscreen();
        }

        // S - Toggle Sidebar
        if (e.key === 's' && !e.target.matches('input, textarea')) {
            e.preventDefault();
            toggleSidebar();
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
    // Inicializar relógio
    updateClock();
    updateDate();
    setInterval(updateClock, 1000);
    setInterval(updateDate, 60000);

    // Inicializar atalhos de teclado
    initKeyboardShortcuts();

    // Inicializar handlers dos cards
    initCardHandlers();

    // Toast de inicialização
    setTimeout(() => {
        showToast('Sistema inicializado', 'success');
    }, 500);

    // Log de inicialização
    console.log('SISCOR High-Tech Interface initialized');
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
    showLoading,
    hideLoading,
    switchLayer,
    toggleFullscreen,
    showDetail,
    refreshData,
    showNotifications,
    showSettings,
    zoomIn,
    zoomOut,
    resetView,
    locateUser,
    fetchData,
    initWebSocket,
    toggleCard,
};

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
