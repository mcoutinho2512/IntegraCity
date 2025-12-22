/**
 * theme_toggle.js - Sistema de Tema Claro/Escuro
 */
let currentTheme = 'light';

function initThemeToggle() {
    console.log('🌙 Inicializando theme toggle...');
    
    // Carregar tema salvo
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
    
    // Adicionar event listener ao botão (ID, não classe!)
    const themeButton = document.getElementById('theme-toggle');
    if (themeButton) {
        themeButton.addEventListener('click', toggleTheme);
        console.log('✅ Botão de tema conectado');
    } else {
        console.error('❌ Botão theme-toggle não encontrado');
    }
}

function toggleTheme() {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
}

function applyTheme(theme) {
    currentTheme = theme;
    
    // Aplicar classe no body
    if (theme === 'dark') {
        document.body.classList.add('dark-theme');
        updateThemeButton('bi-sun-fill', 'Tema');
    } else {
        document.body.classList.remove('dark-theme');
        updateThemeButton('bi-moon-fill', 'Tema');
    }
    
    // Salvar preferência
    localStorage.setItem('theme', theme);
    console.log('✅ Tema alterado para:', theme);
}

function updateThemeButton(iconClass, text) {
    const button = document.getElementById('theme-toggle');
    if (button) {
        const icon = button.querySelector('i');
        const span = button.querySelector('span');
        
        if (icon) {
            icon.className = `bi ${iconClass}`;
        }
        
        if (span) {
            span.textContent = text;
        }
    }
}

// Inicializar quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initThemeToggle);
} else {
    initThemeToggle();
}

console.log('✅ theme_toggle.js carregado');