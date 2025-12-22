/**
 * Sistema de Notificações Avançado - Sirenes, Chuva e Waze
 * Com histórico e armazenamento local
 */

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.historico = [];
        this.unreadCount = 0;
        this.panel = null;
        this.button = null;
        this.modoAtual = 'ativas'; // 'ativas' ou 'historico'
        this.init();
    }

    init() {
        console.log('🔔 Inicializando sistema de notificações...');

        this.panel = document.getElementById('notification-panel');
        this.button = document.getElementById('notifications-toggle');

        if (!this.panel || !this.button) {
            console.error('❌ Painel ou botão não encontrado!');
            return;
        }

        console.log('✅ Painel e botão encontrados');

        // Carregar histórico do localStorage
        this.carregarHistorico();

        this.bindEvents();
        this.loadNotifications();

        // Atualizar a cada 30 segundos
        setInterval(() => this.loadNotifications(), 30000);

        console.log('✅ Sistema de notificações inicializado');
    }

    bindEvents() {
        if (!this.button || !this.panel) return;

        const newButton = this.button.cloneNode(true);
        this.button.parentNode.replaceChild(newButton, this.button);
        this.button = newButton;

        this.button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.togglePanel();
        });

        document.addEventListener('click', (e) => {
            if (this.panel.style.display === 'block' &&
                !this.panel.contains(e.target) &&
                !this.button.contains(e.target)) {
                this.closePanel();
            }
        });

        const closeBtn = this.panel.querySelector('.btn-close-notification');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closePanel();
            });
        }

        console.log('✅ Event listeners configurados');
    }

    togglePanel() {
        if (this.panel.style.display === 'none' || !this.panel.style.display) {
            this.openPanel();
        } else {
            this.closePanel();
        }
    }

    openPanel() {
        this.panel.style.display = 'block';
        console.log('🔓 Painel ABERTO');
    }

    closePanel() {
        this.panel.style.display = 'none';
        console.log('🔒 Painel FECHADO');
    }

    async loadNotifications() {
        console.log('🔄 Carregando notificações...');
        const notificacoesAntigas = [...this.notifications];
        this.notifications = [];

        try {
            const [sirenesData, chuvaData, wazeData, ocorrenciasData] = await Promise.all([
                fetch('/api/sirenes/').then(r => r.json()).catch(() => ({ success: false })),
                fetch('/api/pluviometros/').then(r => r.json()).catch(() => ({ success: false })),
                fetch('/api/waze/').then(r => r.json()).catch(() => ({ success: false })),
                fetch('/api/ocorrencias/tempo-real/').then(r => r.json()).catch(() => ({ success: false }))
            ]);

            // Processar Sirenes
            if (sirenesData.success && sirenesData.data) {
                sirenesData.data.forEach(sirene => {
                    if (sirene.status === 'ativa' || sirene.status === 'teste') {
                        this.notifications.push({
                            id: `sirene-${sirene.id}`,
                            tipo: 'sirene',
                            titulo: sirene.status === 'teste' ? 'Sirene em Teste' : 'Sirene Ativada',
                            mensagem: sirene.nome || sirene.localizacao || 'Sirene sem localização',
                            icon: 'bi-megaphone-fill',
                            cor: sirene.status === 'teste' ? '#f59e0b' : '#ef4444',
                            timestamp: new Date(),
                            dados: sirene
                        });
                    }
                });
            }

            // Processar Chuva
            if (chuvaData.success && chuvaData.data) {
                chuvaData.data.forEach(pluv => {
                    const chuva1h = pluv.chuva_1h || 0;

                    if (chuva1h > 10) {
                        let nivel = '', cor = '#3b82f6';

                        if (chuva1h >= 50) {
                            nivel = 'Chuva Muito Forte';
                            cor = '#dc2626';
                        } else if (chuva1h >= 25) {
                            nivel = 'Chuva Forte';
                            cor = '#ef4444';
                        } else if (chuva1h >= 10) {
                            nivel = 'Chuva Moderada';
                            cor = '#f59e0b';
                        }

                        this.notifications.push({
                            id: `chuva-${pluv.id}`,
                            tipo: 'chuva',
                            titulo: nivel,
                            mensagem: `${pluv.nome || 'Pluviômetro'}: ${chuva1h.toFixed(1)}mm na última hora`,
                            icon: 'bi-cloud-rain-fill',
                            cor: cor,
                            timestamp: new Date(),
                            dados: pluv
                        });
                    }
                });
            }

            // Processar Ocorrências
            if (ocorrenciasData.success && ocorrenciasData.data) {
                ocorrenciasData.data.forEach(occ => {
                    // Mapear prioridade para cor
                    let cor = '#f59e0b'; // Amarelo padrão
                    if (occ.prio === 'MUITO ALTA' || occ.prio === 'ALTA') {
                        cor = '#ef4444'; // Vermelho
                    } else if (occ.prio === 'MÉDIA') {
                        cor = '#f59e0b'; // Amarelo
                    } else {
                        cor = '#10b981'; // Verde
                    }

                    // Mapear tipo para ícone
                    let icone = 'bi-exclamation-circle-fill';
                    const tipo = occ.incidente?.toUpperCase() || '';

                    if (tipo.includes('ACIDENTE')) icone = 'bi-car-front-fill';
                    else if (tipo.includes('INCENDIO') || tipo.includes('INCÊNDIO')) icone = 'bi-fire';
                    else if (tipo.includes('ALAGAMENTO') || tipo.includes('ÁGUA')) icone = 'bi-water';
                    else if (tipo.includes('ÁRVORE')) icone = 'bi-tree-fill';
                    else if (tipo.includes('DESLIZAMENTO')) icone = 'bi-exclamation-triangle-fill';

                    this.notifications.push({
                        id: `ocorrencia-${occ.id}`,
                        tipo: 'ocorrencia',
                        titulo: occ.incidente || 'Ocorrência',
                        mensagem: occ.location || 'Localização não especificada',
                        icon: icone,
                        cor: cor,
                        timestamp: new Date(occ.data || new Date()),
                        dados: occ
                    });
                });
            }
            // Processar Waze - Acidentes e Congestionamentos
            if (wazeData.success) {
                // Processar Acidentes (limite 3)
                if (wazeData.alertas) {
                    const acidentes = wazeData.alertas.filter(a =>
                        a.tipo && a.tipo.toLowerCase().includes('accident')
                    ).slice(0, 3);

                    acidentes.forEach((alerta, index) => {
                        this.notifications.push({
                            id: `waze-acidente-${index}`,
                            tipo: 'waze_acidente',
                            titulo: 'Acidente Reportado',
                            mensagem: alerta.rua || alerta.subtipo || 'Localização não especificada',
                            icon: 'bi-exclamation-triangle-fill',
                            cor: '#ef4444',
                            timestamp: new Date(),
                            dados: alerta
                        });
                    });
                }

                // Processar Congestionamentos (limite 5 - apenas os mais severos)
                if (wazeData.congestionamentos) {
                    const congestSeveros = wazeData.congestionamentos
                        .filter(jam => jam.delay && jam.delay >= 120) // Apenas com delay >= 2 minutos
                        .sort((a, b) => (b.delay || 0) - (a.delay || 0)) // Ordenar por delay
                        .slice(0, 5); // Top 5 piores

                    congestSeveros.forEach((jam, index) => {
                        // Determinar severidade
                        let nivel = 'MODERADO';
                        let cor = '#f59e0b'; // Amarelo

                        if (jam.delay >= 600) { // >= 10 minutos
                            nivel = 'SEVERO';
                            cor = '#ef4444'; // Vermelho
                        } else if (jam.delay >= 300) { // >= 5 minutos
                            nivel = 'ALTO';
                            cor = '#f97316'; // Laranja
                        }

                        // Calcular comprimento em metros
                        const comprimento = jam.length || 0;
                        const comprimentoKm = (comprimento / 1000).toFixed(1);

                        this.notifications.push({
                            id: `waze-jam-${index}`,
                            tipo: 'waze_congestionamento',
                            titulo: `Congestionamento ${nivel}`,
                            mensagem: jam.rua || jam.street || 'Via não especificada',
                            icon: 'bi-stoplights-fill',
                            cor: cor,
                            timestamp: new Date(),
                            dados: {
                                ...jam,
                                nivel: nivel,
                                delay_minutos: Math.round(jam.delay / 60),
                                comprimento_km: comprimentoKm,
                                velocidade: jam.speed || 0
                            }
                        });
                    });
                }
            }

            // Detectar notificações que sumiram (foram para histórico)
            notificacoesAntigas.forEach(antiga => {
                const aindaAtiva = this.notifications.find(n => n.id === antiga.id);
                if (!aindaAtiva) {
                    // Adicionar ao histórico com status "resolvida"
                    this.adicionarAoHistorico({
                        ...antiga,
                        timestampFim: new Date(),
                        status: 'resolvida'
                    });
                }
            });

            console.log(`✅ ${this.notifications.length} notificações ativas`);
            console.log(`   📢 Sirenes: ${this.notifications.filter(n => n.tipo === 'sirene').length}`);
            console.log(`   🌧️ Chuva: ${this.notifications.filter(n => n.tipo === 'chuva').length}`);
            console.log(`   🚗 Waze Acidentes: ${this.notifications.filter(n => n.tipo === 'waze_acidente').length}`);
            console.log(`   🚦 Waze Congestionamentos: ${this.notifications.filter(n => n.tipo === 'waze_congestionamento').length}`);
            console.log(`   🚨 Ocorrências: ${this.notifications.filter(n => n.tipo === 'ocorrencia').length}`);

            this.updatePanel();
            this.updateBadge(this.notifications.length);

        } catch (error) {
            console.error('❌ Erro ao carregar notificações:', error);
            this.updateBadge(0);
        }
    }

    adicionarAoHistorico(notificacao) {
        // Adicionar no início do array
        this.historico.unshift(notificacao);

        // Limitar a 50 no histórico
        if (this.historico.length > 50) {
            this.historico = this.historico.slice(0, 50);
        }

        // Salvar no localStorage
        this.salvarHistorico();
    }

    salvarHistorico() {
        try {
            localStorage.setItem('cor_notificacoes_historico', JSON.stringify(this.historico));
        } catch (e) {
            console.warn('Não foi possível salvar histórico:', e);
        }
    }

    carregarHistorico() {
        try {
            const dados = localStorage.getItem('cor_notificacoes_historico');
            if (dados) {
                this.historico = JSON.parse(dados);
                // Converter strings de data de volta para objetos Date
                this.historico = this.historico.map(n => ({
                    ...n,
                    timestamp: new Date(n.timestamp),
                    timestampFim: n.timestampFim ? new Date(n.timestampFim) : null
                }));
                console.log(`📚 ${this.historico.length} notificações carregadas do histórico`);
            }
        } catch (e) {
            console.warn('Erro ao carregar histórico:', e);
            this.historico = [];
        }
    }

    limparHistorico() {
        if (confirm('Tem certeza que deseja limpar todo o histórico?')) {
            this.historico = [];
            this.salvarHistorico();
            if (this.modoAtual === 'historico') {
                this.updatePanel();
            }
            console.log('🗑️ Histórico limpo');
        }
    }

    updatePanel() {
        const body = document.getElementById('notification-body');
        if (!body) return;

        // Criar header com botões
        const header = this.criarHeaderComBotoes();

        // Determinar qual lista mostrar
        const lista = this.modoAtual === 'ativas' ? this.notifications : this.historico;

        if (lista.length === 0) {
            body.innerHTML = header + this.criarEstadoVazio();
            return;
        }

        const notificacoesHTML = lista.map((notif, index) =>
            this.criarNotificacaoHTML(notif, index)
        ).join('');

        body.innerHTML = header + notificacoesHTML;

        // Adicionar event listeners aos botões
        this.adicionarEventListenersBotoes();

        // Adicionar CSS se necessário
        this.adicionarEstilos();
    }

    criarHeaderComBotoes() {
        return `
        <div style="
            display: flex;
            gap: 6px;
            margin-bottom: 12px;
            padding: 8px;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.6) 100%);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            position: sticky;
            top: 0;
            z-index: 10;
            backdrop-filter: blur(10px);
        ">
            <button id="btn-ativas" class="modo-btn" data-modo="ativas" style="
                flex: 1;
                padding: 8px 12px;
                background: ${this.modoAtual === 'ativas' ? 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)' : 'rgba(51, 65, 85, 0.5)'};
                color: white;
                border: ${this.modoAtual === 'ativas' ? '2px solid rgba(59, 130, 246, 0.5)' : '1px solid rgba(255, 255, 255, 0.1)'};
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
                box-shadow: ${this.modoAtual === 'ativas' ? '0 4px 12px rgba(59, 130, 246, 0.3)' : 'none'};
            ">
                <i class="bi bi-activity" style="font-size: 14px;"></i>
                <span>Ativas</span>
                <span style="
                    background: ${this.modoAtual === 'ativas' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.1)'};
                    padding: 2px 6px;
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: 700;
                    min-width: 20px;
                ">${this.notifications.length}</span>
            </button>
            
            <button id="btn-historico" class="modo-btn" data-modo="historico" style="
                flex: 1;
                padding: 8px 12px;
                background: ${this.modoAtual === 'historico' ? 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)' : 'rgba(51, 65, 85, 0.5)'};
                color: white;
                border: ${this.modoAtual === 'historico' ? '2px solid rgba(139, 92, 246, 0.5)' : '1px solid rgba(255, 255, 255, 0.1)'};
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
                box-shadow: ${this.modoAtual === 'historico' ? '0 4px 12px rgba(139, 92, 246, 0.3)' : 'none'};
            ">
                <i class="bi bi-clock-history" style="font-size: 14px;"></i>
                <span>Histórico</span>
                <span style="
                    background: ${this.modoAtual === 'historico' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.1)'};
                    padding: 2px 6px;
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: 700;
                    min-width: 20px;
                ">${this.historico.length}</span>
            </button>
            
            ${this.modoAtual === 'historico' && this.historico.length > 0 ? `
                <button id="btn-limpar-historico" style="
                    padding: 8px 10px;
                    background: rgba(239, 68, 68, 0.15);
                    color: #ef4444;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                " title="Limpar histórico">
                    <i class="bi bi-trash" style="font-size: 14px;"></i>
                </button>
            ` : ''}
        </div>
    `;
    }

    criarEstadoVazio() {
        if (this.modoAtual === 'ativas') {
            return `
                <div style="text-align: center; padding: 60px 20px;">
                    <div style="
                        width: 80px;
                        height: 80px;
                        margin: 0 auto 24px;
                        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                    ">
                        <i class="bi bi-check-circle" style="font-size: 36px; color: #10b981;"></i>
                    </div>
                    <h4 style="color: #94a3b8; margin: 0 0 8px 0; font-size: 16px; font-weight: 600;">
                        Tudo Tranquilo!
                    </h4>
                    <p style="color: #64748b; margin: 0; font-size: 14px;">
                        Nenhuma notificação ativa no momento
                    </p>
                </div>
            `;
        } else {
            return `
                <div style="text-align: center; padding: 60px 20px;">
                    <div style="
                        width: 80px;
                        height: 80px;
                        margin: 0 auto 24px;
                        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                    ">
                        <i class="bi bi-archive" style="font-size: 36px; color: #64748b;"></i>
                    </div>
                    <h4 style="color: #94a3b8; margin: 0 0 8px 0; font-size: 16px; font-weight: 600;">
                        Histórico Vazio
                    </h4>
                    <p style="color: #64748b; margin: 0; font-size: 14px;">
                        Nenhuma notificação anterior registrada
                    </p>
                </div>
            `;
        }
    }

    criarNotificacaoHTML(notif, index) {
        const tempoAtras = this.getTempoDecorrido(notif.timestamp);
        const duracao = notif.timestampFim ? this.getDuracao(notif.timestamp, notif.timestampFim) : null;
        const ehHistorico = this.modoAtual === 'historico';

        let bgGradient = '';
        switch (notif.tipo) {
            case 'sirene':
                bgGradient = ehHistorico ?
                    'linear-gradient(135deg, rgba(100, 116, 139, 0.06) 0%, rgba(71, 85, 105, 0.04) 100%)' :
                    'linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(220, 38, 38, 0.05) 100%)';
                break;
            case 'chuva':
                bgGradient = ehHistorico ?
                    'linear-gradient(135deg, rgba(100, 116, 139, 0.06) 0%, rgba(71, 85, 105, 0.04) 100%)' :
                    'linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(37, 99, 235, 0.05) 100%)';
                break;
            case 'ocorrencia':
                bgGradient = ehHistorico ?
                    'linear-gradient(135deg, rgba(100, 116, 139, 0.06) 0%, rgba(71, 85, 105, 0.04) 100%)' :
                    'linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(217, 119, 6, 0.05) 100%)';
                break;
            case 'waze':
                bgGradient = ehHistorico ?
                    'linear-gradient(135deg, rgba(100, 116, 139, 0.06) 0%, rgba(71, 85, 105, 0.04) 100%)' :
                    'linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(217, 119, 6, 0.05) 100%)';
                break;
            default:
                bgGradient = 'linear-gradient(135deg, rgba(100, 116, 139, 0.08) 0%, rgba(71, 85, 105, 0.05) 100%)';
            case 'waze_acidente':
            case 'waze_congestionamento':
                bgGradient = ehHistorico ?
                    'linear-gradient(135deg, rgba(100, 116, 139, 0.06) 0%, rgba(71, 85, 105, 0.04) 100%)' :
                    'linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(217, 119, 6, 0.05) 100%)';
                break;
        }

        const corFinal = ehHistorico ? '#64748b' : notif.cor;

        // Informações adicionais por tipo
        let infoExtra = '';

        if (notif.tipo === 'sirene') {
            infoExtra = `
            <div style="display: flex; gap: 6px; font-size: 11px; color: #94a3b8; margin-top: 4px;">
                <span><i class="bi bi-geo-alt-fill"></i> ${notif.dados?.bairro || 'Localização'}</span>
                ${notif.dados?.prioridade ? `<span>•</span><span><i class="bi bi-flag-fill"></i> ${notif.dados.prioridade}</span>` : ''}
            </div>
        `;
        } else if (notif.tipo === 'chuva') {
            const chuva = notif.dados;
            infoExtra = `
            <div style="display: flex; gap: 8px; font-size: 11px; margin-top: 4px;">
                <span style="color: #60a5fa;"><i class="bi bi-droplet-fill"></i> 1h: ${chuva?.chuva_1h || 0}mm</span>
                <span style="color: #3b82f6;"><i class="bi bi-droplet-half"></i> 4h: ${chuva?.chuva_4h || 0}mm</span>
                <span style="color: #2563eb;"><i class="bi bi-cloud-drizzle-fill"></i> 24h: ${chuva?.chuva_24h || 0}mm</span>
            </div>
        `;
        } else if (notif.tipo === 'ocorrencia') {
            const occ = notif.dados;
            infoExtra = `
            <div style="display: flex; gap: 6px; font-size: 11px; color: #94a3b8; margin-top: 4px; flex-wrap: wrap;">
                ${occ?.bairro ? `<span><i class="bi bi-geo-alt-fill"></i> ${occ.bairro}</span>` : ''}
                ${occ?.prio ? `<span>•</span><span style="color: ${corFinal}; font-weight: 600;"><i class="bi bi-exclamation-triangle-fill"></i> ${occ.prio}</span>` : ''}
                ${occ?.status ? `<span>•</span><span><i class="bi bi-circle-fill" style="font-size: 6px;"></i> ${occ.status}</span>` : ''}
            </div>
        `;
        } else if (notif.tipo === 'waze_acidente') {
            infoExtra = `
        <div style="display: flex; gap: 6px; font-size: 11px; color: #94a3b8; margin-top: 4px;">
            <span><i class="bi bi-car-front-fill"></i> Acidente</span>
            ${notif.dados?.subtipo ? `<span>•</span><span>${notif.dados.subtipo}</span>` : ''}
            <span>•</span>
            <span><i class="bi bi-clock"></i> ${tempoAtras}</span>
        </div>
    `;
        } else if (notif.tipo === 'waze_congestionamento') {
            const jam = notif.dados;
            infoExtra = `
        <div style="display: flex; gap: 8px; font-size: 11px; margin-top: 4px; flex-wrap: wrap;">
            <span style="color: ${corFinal}; font-weight: 600;">
                <i class="bi bi-clock-fill"></i> Atraso: ${jam.delay_minutos}min
            </span>
            <span style="color: #94a3b8;">
                <i class="bi bi-rulers"></i> ${jam.comprimento_km}km
            </span>
            ${jam.velocidade ? `
                <span style="color: #94a3b8;">
                    <i class="bi bi-speedometer2"></i> ${Math.round(jam.velocidade)}km/h
                </span>
            ` : ''}
        </div>
    `;
        }

        return `
        <div class="notification-item" style="
            background: ${bgGradient};
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-left: 3px solid ${corFinal};
            border-radius: 10px;
            padding: 10px 12px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            animation: slideIn 0.4s ease-out ${index * 0.05}s both;
            ${ehHistorico ? 'opacity: 0.7;' : ''}
        " 
        onmouseover="this.style.transform='translateX(4px)'; this.style.boxShadow='0 4px 16px rgba(0, 0, 0, 0.2)'; ${ehHistorico ? 'this.style.opacity=1;' : ''}" 
        onmouseout="this.style.transform='translateX(0)'; this.style.boxShadow='0 2px 8px rgba(0, 0, 0, 0.1)'; ${ehHistorico ? 'this.style.opacity=0.7;' : ''}">
            
            <div style="display: flex; align-items: flex-start; gap: 10px;">
                <!-- Ícone compacto -->
                <div style="
                    width: 36px;
                    height: 36px;
                    background: ${corFinal};
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                    box-shadow: 0 2px 8px ${corFinal}40;
                    position: relative;
                    ${ehHistorico ? 'opacity: 0.6;' : ''}
                ">
                    <i class="bi ${notif.icon}" style="color: white; font-size: 16px;"></i>
                    ${!ehHistorico && notif.tipo === 'sirene' ? `
                        <div style="
                            position: absolute;
                            width: 100%;
                            height: 100%;
                            border-radius: 8px;
                            animation: pulse 2s infinite;
                        "></div>
                    ` : ''}
                    ${ehHistorico ? `
                        <div style="
                            position: absolute;
                            top: -3px;
                            right: -3px;
                            width: 14px;
                            height: 14px;
                            background: #10b981;
                            border: 2px solid #0f172a;
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        ">
                            <i class="bi bi-check" style="color: white; font-size: 8px;"></i>
                        </div>
                    ` : ''}
                </div>
                
                <!-- Conteúdo compacto -->
                <div style="flex: 1; min-width: 0;">
                    <!-- Header com título e badges -->
                    <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px; flex-wrap: wrap;">
                        <strong style="
                            color: ${ehHistorico ? '#cbd5e1' : '#f8fafc'};
                            font-size: 13px;
                            font-weight: 600;
                            letter-spacing: -0.01em;
                        ">${notif.titulo}</strong>
                        
                        <!-- Badge de categoria -->
                        <span style="
                            display: inline-flex;
                            align-items: center;
                            gap: 4px;
                            font-size: 9px;
                            color: ${corFinal};
                            background: ${corFinal}15;
                            padding: 2px 6px;
                            border-radius: 4px;
                            font-weight: 700;
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                        ">
                            <span style="
                                width: 4px;
                                height: 4px;
                                background: ${corFinal};
                                border-radius: 50%;
                                ${!ehHistorico ? 'animation: blink 2s infinite;' : ''}
                            "></span>
                            ${notif.tipo === 'sirene' ? 'ALERTA' :
                notif.tipo === 'chuva' ? 'METEO' :
                    notif.tipo === 'waze_acidente' ? 'ACIDENTE' :
                        notif.tipo === 'waze_congestionamento' ? 'TRÂNSITO' :
                            notif.tipo === 'ocorrencia' ? 'OCORRÊNCIA' : 'INFO'}
                        </span>
                        
                        <!-- Tempo -->
                        <span style="
                            font-size: 9px;
                            color: #64748b;
                            font-weight: 600;
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                            background: rgba(100, 116, 139, 0.1);
                            padding: 2px 6px;
                            border-radius: 4px;
                            margin-left: auto;
                        ">${tempoAtras}</span>
                        
                        ${duracao ? `
                            <span style="
                                font-size: 9px;
                                color: #10b981;
                                font-weight: 600;
                                background: rgba(16, 185, 129, 0.15);
                                padding: 2px 6px;
                                border-radius: 4px;
                            "><i class="bi bi-clock"></i> ${duracao}</span>
                        ` : ''}
                    </div>
                    
                    <!-- Mensagem compacta -->
                    <p style="
                        margin: 0 0 4px 0;
                        color: ${ehHistorico ? '#94a3b8' : '#cbd5e1'};
                        font-size: 12px;
                        line-height: 1.4;
                        display: -webkit-box;
                        -webkit-line-clamp: 1;
                        -webkit-box-orient: vertical;
                        overflow: hidden;
                    ">${notif.mensagem}</p>
                    
                    <!-- Informações extras -->
                    ${infoExtra}
                    
                    ${ehHistorico ? `
                        <div style="margin-top: 6px;">
                            <span style="
                                display: inline-flex;
                                align-items: center;
                                gap: 4px;
                                font-size: 10px;
                                color: #10b981;
                                background: rgba(16, 185, 129, 0.15);
                                padding: 3px 8px;
                                border-radius: 4px;
                                font-weight: 600;
                            ">
                                <i class="bi bi-check-circle-fill"></i>
                                RESOLVIDA
                            </span>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
    }

    adicionarEventListenersBotoes() {
        // Usar delegação de eventos para garantir que funciona sempre
        const body = document.getElementById('notification-body');
        if (!body) return;

        // Remover listeners antigos
        const oldListener = body._clickListener;
        if (oldListener) {
            body.removeEventListener('click', oldListener);
        }

        // Criar novo listener
        const clickListener = (e) => {
            const target = e.target.closest('button');
            if (!target) return;

            // CRITICAL: Impedir que o click propague e feche o painel
            e.stopPropagation();
            e.preventDefault();

            const modo = target.dataset.modo;

            if (modo === 'ativas') {
                console.log('🟢 Mudando para: Ativas');
                this.modoAtual = 'ativas';
                this.updatePanel();
            } else if (modo === 'historico') {
                console.log('🟣 Mudando para: Histórico');
                this.modoAtual = 'historico';
                this.updatePanel();
            } else if (target.id === 'btn-limpar-historico') {
                console.log('🗑️ Limpar histórico');
                this.limparHistorico();
            }
        };

        // Adicionar novo listener
        body.addEventListener('click', clickListener);
        body._clickListener = clickListener;

        console.log(`✅ Event listeners configurados para modo: ${this.modoAtual}`);
    }

    adicionarEstilos() {
        if (document.getElementById('notification-animations')) return;

        const style = document.createElement('style');
        style.id = 'notification-animations';
        style.textContent = `
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateX(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            @keyframes pulse {
                0%, 100% {
                    opacity: 1;
                }
                50% {
                    opacity: 0.5;
                }
            }
            
            @keyframes blink {
                0%, 100% {
                    opacity: 1;
                }
                50% {
                    opacity: 0.3;
                }
            }
            
            .notification-item:active {
                transform: scale(0.98) !important;
            }
            
            #notification-body::-webkit-scrollbar {
                width: 6px;
            }
            
            #notification-body::-webkit-scrollbar-track {
                background: rgba(15, 23, 42, 0.3);
                border-radius: 10px;
            }
            
            #notification-body::-webkit-scrollbar-thumb {
                background: rgba(100, 116, 139, 0.5);
                border-radius: 10px;
            }
            
            #notification-body::-webkit-scrollbar-thumb:hover {
                background: rgba(100, 116, 139, 0.7);
            }
        `;
        document.head.appendChild(style);
    }

    updateBadge(count) {
        this.unreadCount = count;

        if (this.button) {
            const badge = this.button.querySelector('.notification-count');
            if (badge) {
                badge.textContent = count;
                badge.style.display = count > 0 ? 'flex' : 'none';
            }
        }
    }

    getTempoDecorrido(timestamp) {
        const agora = new Date();
        const diff = Math.floor((agora - timestamp) / 1000);

        if (diff < 60) return 'agora';
        if (diff < 3600) return `${Math.floor(diff / 60)}min`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
        return `${Math.floor(diff / 86400)}d`;
    }

    getDuracao(inicio, fim) {
        const diff = Math.floor((fim - inicio) / 1000);

        if (diff < 60) return `${diff}s`;
        if (diff < 3600) return `${Math.floor(diff / 60)}min`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}min`;
        return `${Math.floor(diff / 86400)}d`;
    }
}

// Inicializar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.notificationSystem = new NotificationSystem();
    });
} else {
    window.notificationSystem = new NotificationSystem();
}

console.log('✅ notifications.js carregado - Sistema avançado com histórico');