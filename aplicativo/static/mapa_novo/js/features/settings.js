/**
 * settings.js - Sistema de Configurações
 */

class SettingsManager {
    constructor() {
        this.settings = this.loadSettings();
        this.init();
    }

    init() {
        this.createModal();
        this.attachEvents();
        this.applySettings();
    }

    loadSettings() {
        const saved = localStorage.getItem('cor_settings');
        return saved ? JSON.parse(saved) : {
            darkMode: false,
            notifications: true,
            sound: true,
            autoRefresh: true,
            refreshInterval: 30
        };
    }

    saveSettings() {
        localStorage.setItem('cor_settings', JSON.stringify(this.settings));
    }

    createModal() {
        const modal = document.createElement('div');
        modal.className = 'settings-modal';
        modal.id = 'settings-modal';
        modal.innerHTML = '<div class="settings-content"><div class="settings-header"><div class="settings-title"><i class="bi bi-gear-fill"></i>Configurações</div><button class="settings-close" id="settings-close"><i class="bi bi-x-lg"></i></button></div><div class="settings-body"><div class="settings-section"><div class="settings-section-title">Aparência</div><div class="settings-option"><div class="settings-option-info"><div class="settings-option-label">Tema Escuro</div><div class="settings-option-desc">Ativar modo escuro</div></div><div class="settings-toggle" data-setting="darkMode"></div></div></div><div class="settings-section"><div class="settings-section-title">Notificações</div><div class="settings-option"><div class="settings-option-info"><div class="settings-option-label">Alertas</div><div class="settings-option-desc">Receber notificações de alertas</div></div><div class="settings-toggle" data-setting="notifications"></div></div><div class="settings-option"><div class="settings-option-info"><div class="settings-option-label">Som</div><div class="settings-option-desc">Tocar som nas notificações</div></div><div class="settings-toggle" data-setting="sound"></div></div></div><div class="settings-section"><div class="settings-section-title">Atualização</div><div class="settings-option"><div class="settings-option-info"><div class="settings-option-label">Auto Refresh</div><div class="settings-option-desc">Atualizar dados automaticamente</div></div><div class="settings-toggle" data-setting="autoRefresh"></div></div></div></div></div></div>';
        
        document.body.appendChild(modal);
    }

    attachEvents() {
        // Abrir modal
        const gearBtns = document.querySelectorAll('[title="Configurações"]');
        gearBtns.forEach(btn => {
            btn.addEventListener('click', () => this.openModal());
        });

        // Fechar modal
        const modal = document.getElementById('settings-modal');
        const closeBtn = document.getElementById('settings-close');
        
        closeBtn.addEventListener('click', () => this.closeModal());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeModal();
        });

        // Toggles
        document.querySelectorAll('.settings-toggle').forEach(toggle => {
            const setting = toggle.dataset.setting;
            if (this.settings[setting]) {
                toggle.classList.add('active');
            }
            
            toggle.addEventListener('click', () => {
                this.settings[setting] = !this.settings[setting];
                toggle.classList.toggle('active');
                this.saveSettings();
                this.applySettings();
            });
        });
    }

    openModal() {
        document.getElementById('settings-modal').classList.add('active');
    }

    closeModal() {
        document.getElementById('settings-modal').classList.remove('active');
    }

    applySettings() {
        // Dark mode
        if (this.settings.darkMode) {
            document.body.classList.add('dark-theme');
            const icon = document.querySelector('#theme-toggle i');
            if (icon) {
                icon.className = 'bi bi-sun-fill';
            }
        } else {
            document.body.classList.remove('dark-theme');
            const icon = document.querySelector('#theme-toggle i');
            if (icon) {
                icon.className = 'bi bi-moon-fill';
            }
        }
    }

    toggleDarkMode() {
        this.settings.darkMode = !this.settings.darkMode;
        this.saveSettings();
        this.applySettings();
        
        // Atualizar toggle no modal
        const toggle = document.querySelector('[data-setting="darkMode"]');
        if (toggle) {
            toggle.classList.toggle('active', this.settings.darkMode);
        }
    }
}

// Inicializar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.settingsManager = new SettingsManager();
    });
} else {
    window.settingsManager = new SettingsManager();
}

console.log('settings.js carregado');
