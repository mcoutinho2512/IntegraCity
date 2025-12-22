/**
 * map_utils.js - Utilitários do Mapa
 */

const PRIORITY_COLORS = {
    muito_alta: '#dc3545',
    alta: '#fd7e14',
    media: '#ffc107',
    baixa: '#28a745',
    ativa: '#dc3545',
    inativa: '#6c757d'
};

const ICON_CLASSES = {
    sirene: 'bi-megaphone-fill',
    evento: 'bi-calendar-event-fill',
    ocorrencia: 'bi-exclamation-triangle-fill',
    alagamento: 'bi-water',
    escola: 'bi-building',
    hospital: 'bi-hospital-fill'
};

function createCustomDivIcon(type, priority, size) {
    const iconClass = ICON_CLASSES[type] || 'bi-geo-alt-fill';
    const color = PRIORITY_COLORS[priority] || PRIORITY_COLORS.media;
    
    const html = '<div class="custom-marker" style="width:' + size + 'px;height:' + size + 'px;background-color:' + color + ';border:3px solid white;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.3)"><i class="bi ' + iconClass + '" style="font-size:' + (size * 0.5) + 'px;color:white"></i></div>';
    
    return L.divIcon({
        html: html,
        className: 'custom-div-icon',
        iconSize: [size, size],
        iconAnchor: [size/2, size/2],
        popupAnchor: [0, -size/2]
    });
}

function createPulsingIcon(type, priority, size) {
    const iconClass = ICON_CLASSES[type] || 'bi-geo-alt-fill';
    const color = PRIORITY_COLORS[priority] || PRIORITY_COLORS.alta;
    
    const html = '<div class="pulsing-marker" style="position:relative;width:' + size + 'px;height:' + size + 'px"><div class="pulse-ring" style="position:absolute;width:100%;height:100%;border:3px solid ' + color + ';border-radius:50%;animation:pulse 2s infinite;opacity:0"></div><div class="marker-core" style="position:absolute;width:100%;height:100%;background-color:' + color + ';border:3px solid white;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.3);z-index:1"><i class="bi ' + iconClass + '" style="font-size:' + (size * 0.5) + 'px;color:white"></i></div></div>';
    
    return L.divIcon({
        html: html,
        className: 'pulsing-div-icon',
        iconSize: [size, size],
        iconAnchor: [size/2, size/2],
        popupAnchor: [0, -size/2]
    });
}

function formatData(dateString) {
    if (!dateString) return 'Data não disponível';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getColorByPriority(priority) {
    return PRIORITY_COLORS[priority] || PRIORITY_COLORS.media;
}

function addMarkerStyles() {
    if (document.getElementById('marker-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'marker-styles';
    style.textContent = '.custom-div-icon, .pulsing-div-icon { background: none !important; border: none !important; } @keyframes pulse { 0% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.5); opacity: 0.5; } 100% { transform: scale(2); opacity: 0; } } .custom-marker:hover, .marker-core:hover { transform: scale(1.1); } .custom-popup .popup-header { padding: 10px; border-radius: 8px 8px 0 0; color: white; font-weight: bold; } .custom-popup .popup-body { padding: 10px; } .custom-popup .popup-title { margin: 0; font-size: 14px; }';
    document.head.appendChild(style);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addMarkerStyles);
} else {
    addMarkerStyles();
}

console.log('✓ map_utils.js carregado');