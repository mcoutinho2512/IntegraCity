#  RELATÓRIO DE MIGRAÇÃO - SISCOR v2.0

##  O QUE FALTA MIGRAR/FAZER

**Data:** 18/10/2025 12:19

---

## 1.  MODELS (BANCO DE DADOS) - PRIORIDADE ALTA

### Total: 264 Models a Migrar

#### Models Críticos do Sistema

##### 🚨 Defesa Civil
- [ ] `Sirene` - Sistema de sirenes de alerta
- [ ] `StatusSirene` - Status das sirenes
- [ ] `HistoricoSirene` - Histórico de acionamentos
- [ ] `AlertaChuva` - Alertas de chuva

#####  Eventos
- [ ] `Evento` - Eventos da cidade
- [ ] `TipoEvento` - Tipos de eventos
- [ ] `LocalEvento` - Locais de eventos

##### ⚠️ Ocorrências
- [ ] `Ocorrencia` - Ocorrências registradas
- [ ] `TipoOcorrencia` - Tipos de ocorrências
- [ ] `StatusOcorrencia` - Status das ocorrências
- [ ] `Alagamento` - Pontos de alagamento

##### 🏫 Locais Importantes
- [ ] `Escola` - Escolas da cidade
- [ ] `Hospital` - Hospitais
- [ ] `AbrInterno` - Abrigos
- [ ] `UnidadeSaude` - Unidades de saúde

##### 🌧️ Meteorologia
- [ ] `EstacaoPluviometrica` - Estações de chuva
- [ ] `DadosChuva` - Medições de chuva
- [ ] `PrevisaoTempo` - Previsão do tempo
- [ ] `Bolsao` - Bolsões de água

#####  Mobilidade Urbana
- [ ] `DadosTransito` - Dados de trânsito
- [ ] `RotaTransito` - Rotas de trânsito
- [ ] `EstagioMobilidade` - Estágios de mobilidade
- [ ] `TransitoNaoUsual` - Tráfego anormal
- [ ] `JamWaze` - Congestionamentos Waze

#####  Monitoramento
- [ ] `CameraCOR` - Câmeras do COR
- [ ] `Camera` - Outras câmeras

#####  Transporte Público
- [ ] `LinhaOnibus` - Linhas de ônibus
- [ ] `PontoOnibus` - Pontos de ônibus
- [ ] `VeiculoTransporte` - Veículos

### Tarefas
- [ ] Copiar todos os models do `aplicativo/models.py`
- [ ] Ajustar imports e dependências
- [ ] Criar migrations: `python manage.py makemigrations`
- [ ] Aplicar migrations: `python manage.py migrate`
- [ ] Popular banco com dados de teste

---

## 2.  VIEWS/APIs - 50 VIEWS A MIGRAR

###  Mobilidade Urbana (12 views)

- [ ] `transito_api(request)` - API principal de trânsito
- [ ] `transito_situacao(request)` - Situação atual do trânsito
- [ ] `estagio_api(request)` - Estágios de mobilidade
- [ ] `estagio_api_app(request)` - Para app mobile
- [ ] `estagio_api_xml(request)` - Formato XML
- [ ] `estagio_mudanca(request, id)` - Mudança de estágio
- [ ] `grafico_transito(request)` - Gráficos de trânsito
- [ ] `unz_api(request)` - Tráfego não usual
- [ ] `rotas_xml(request)` - Lista de rotas XML
- [ ] `rota_xml(request, id)` - Rota específica XML
- [ ] `ttempo_api(request)` - Tempo de viagem
- [ ] `modal_api(request)` - Transporte modal
- [ ] `modal_api_json(request)` - Modal em JSON
- [ ] `transporte_api(request)` - Transporte geral
- [ ] `pa_api(request)` - Áreas de Planejamento

###  Meteorologia (6 views)

- [ ] `chuva_api(request)` - Dados de chuva
- [ ] `previsao_api(request)` - Previsão do tempo
- [ ] `tempo(request)` - Página de tempo
- [ ] `tempo_api(request)` - API de tempo
- [ ] `mar(request)` - Condições marítimas
- [ ] `rios(request)` - Monitoramento de rios

###  Defesa Civil (6 views)

- [ ] `sirenes(request)` - Página de sirenes
- [ ] `sirene_api(request)` - API de sirenes
- [ ] `alerta_api(request)` - API de alerta
- [ ] `alertas_api(request)` - API de alertas (plural)
- [ ] `alertas(request)` - Página de alertas
- [ ] `avisos_api(request)` - Avisos gerais

###  Ocorrências (6 views)

- [ ] `inserir_ocorrencia(request)` - Inserir nova ocorrência
- [ ] `confirmado(request, id)` - Confirmar ocorrência
- [ ] `apurando(request, id)` - Marcar como apurando
- [ ] `descartado(request, id)` - Descartar ocorrência
- [ ] `comando_api_ocorrencias(request)` - Comandos para ocorrências
- [ ] `fotos_api(request)` - API de fotos

###  Eventos (2 views)

- [ ] `eventos(request)` - Lista de eventos
- [ ] `evento_perfil(request, id)` - Perfil do evento

###  Sistema/Geral (18 views)

- [ ] `index(request)` - Página inicial
- [ ] `mapa(request)` - Mapa principal
- [ ] `painel(request)` - Painel de controle
- [ ] `cimu(request)` - CIMU
- [ ] `gig(request)` - GIG
- [ ] `consulta(request)` - Consulta geral
- [ ] `consulta_view(request)` - View de consulta
- [ ] `estagios(request)` - Estágios
- [ ] `inserir_id(request)` - Inserir ID
- [ ] `inserir_locations(request)` - Inserir localizações
- [ ] `download_file(request, id)` - Download de arquivo
- [ ] `alexia_api(request)` - Integração Alexia
- [ ] `comando_api(request)` - Comandos gerais
- [ ] `junto(request)` - Função junto
- [ ] `monthdelta(date, delta)` - Função auxiliar

---

## 3.  URLs - CONFIGURAR ROTAS

### URLs a Criar

\\\python
# Mobilidade Urbana
path('api/transito/', transito_api, name='transito_api'),
path('api/estagio/', estagio_api, name='estagio_api'),
path('api/unz/', unz_api, name='unz_api'),
path('api/rotas/', rotas_xml, name='rotas_xml'),
# ... +11 URLs

# Meteorologia
path('api/chuva/', chuva_api, name='chuva_api'),
path('api/previsao/', previsao_api, name='previsao_api'),
path('api/tempo/', tempo_api, name='tempo_api'),
# ... +3 URLs

# Defesa Civil
path('api/sirenes/', sirene_api, name='sirene_api'),
path('api/alertas/', alertas_api, name='alertas_api'),
# ... +4 URLs

# Ocorrências
path('api/ocorrencias/inserir/', inserir_ocorrencia),
path('api/ocorrencias/confirmado/<int:id>/', confirmado),
# ... +4 URLs

# E mais ~20 URLs...
\\\

---

## 4.  INTEGRAÇÕES COM APIs EXTERNAS

### 30+ Scripts de Coleta de Dados

####  Trânsito
- [ ] `coleta_de_dados/waze.py` - API Noah Smart City/Waze

####  Meteorologia
- [ ] `coleta_de_dados/alertario.py` - Alerta Rio
- [ ] `coleta_de_dados/alertario_chuva.py` - Chuva Alerta Rio
- [ ] `coleta_de_dados/inea_chuva.py` - INEA chuva
- [ ] `coleta_de_dados/inea_rio.py` - INEA rios
- [ ] `coleta_de_dados/defesacivil_chuva.py` - Defesa Civil
- [ ] `coleta_de_dados/niteroi_chuva.py` - Niterói
- [ ] `coleta_de_dados/inmet.py` - INMET
- [ ] `coleta_de_dados/inmet_novo.py` - INMET novo
- [ ] `coleta_de_dados/previsao.py` - Previsão
- [ ] `coleta_de_dados/coletanoaa.py` - NOAA

####  Alertas
- [ ] `coleta_de_dados/sirene.py` - Sirenes

####  Monitoramento
- [ ] `coleta_de_dados/cameras.py` - Câmeras
- [ ] `coleta_de_dados/camera_situ.py` - Situação câmeras
- [ ] `coleta_de_dados/camera_vi.py` - Vídeo inteligente

####  Transporte
- [ ] `coleta_de_dados/frotacor.py` - Frota COR
- [ ] `coleta_de_dados/frotacet.py` - Frota CET
- [ ] `coleta_de_dados/frotacet_novo.py` - Frota CET novo
- [ ] `coleta_de_dados/onibus.py` - Ônibus
- [ ] `coleta_de_dados/brt.py` - BRT
- [ ] `coleta_de_dados/linha.py` - Linhas

####  Outros
- [ ] `coleta_de_dados/mar.py` - Condições do mar
- [ ] `coleta_de_dados/coleta_boia.py` - Boias
- [ ] `coleta_de_dados/fab.py` - FAB
- [ ] `coleta_de_dados/balneabilidade.py` - Balneabilidade
- [ ] `coleta_de_dados/iqar.py` - Qualidade do ar
- [ ] `coleta_de_dados/comlurb.py` - Comlurb
- [ ] `coleta_de_dados/guarda.py` - Guarda Municipal
- [ ] `coleta_de_dados/light.py` - Light (energia)
- [ ] `coleta_de_dados/sppo.py` - SPPO
- [ ] `coleta_de_dados/surfconnect.py` - Surf Connect
- [ ] `coleta_de_dados/twitter_*.py` - Integração Twitter
- [ ] `coleta_de_dados/fotos.py` - Fotos

### Tarefas
- [ ] Migrar scripts de coleta
- [ ] Configurar credenciais de APIs
- [ ] Criar sistema de agendamento (Celery/Cron)
- [ ] Implementar tratamento de erros
- [ ] Logs de coleta

---

## 5.  RECURSOS VISUAIS FALTANTES

### Ícones de Marcadores
- [ ] Sirenes (3 níveis: ativa, média, baixa)
- [ ] Eventos (3 níveis: alta, média, baixa prioridade)
- [ ] Ocorrências (4 níveis: muito alta, alta, média, baixa)
- [ ] Alagamentos (3 níveis: alto, médio, baixo)
- [ ] Hospitais
- [ ] Escolas
- [ ] Apoio/Suporte
- [ ] Feiras

### Criar ou Buscar
- [ ] Gerar ícones SVG customizados
- [ ] Ou copiar de outro projeto
- [ ] Ou usar biblioteca de ícones

---

## 6.  SISTEMA DE TEMPO REAL

### WebSocket
- [ ] Configurar Django Channels
- [ ] Implementar consumers WebSocket
- [ ] Sistema de notificações push
- [ ] Atualização automática de dados
- [ ] Conexão persistente

### JavaScript
- [ ] Cliente WebSocket
- [ ] Reconexão automática
- [ ] Tratamento de mensagens
- [ ] Atualização de marcadores em tempo real

---

## 7.  NAVBAR E NAVEGAÇÃO

### Menu Principal
- [ ] Visão Geral
- [ ] Mobilidade Urbana (dropdown)
  - [ ] Rotas
  - [ ] Trânsito
  - [ ] Trânsito por AP
  - [ ] Histórico de Trânsito
- [ ] Meteorologia (dropdown)
  - [ ] Meteorologia
  - [ ] Pluviômetros
  - [ ] Bolsões
  - [ ] Rios e Lagoas
  - [ ] Sensores de alagamento
  - [ ] Qualidade do Ar
- [ ] Defesa Civil (dropdown)
  - [ ] Sirenes
- [ ] Vídeo Monitoramento (dropdown)
  - [ ] Câmeras
- [ ] Consultas (dropdown)
  - [ ] Relatórios
  - [ ] Históricos

---

## 8.  FUNCIONALIDADES AVANÇADAS

### Dashboard
- [ ] Métricas em tempo real
- [ ] Gráficos interativos (Chart.js)
- [ ] Cards com estatísticas
- [ ] Atualização automática

### Filtros
- [ ] Filtros por tipo
- [ ] Filtros por prioridade
- [ ] Filtros por região
- [ ] Filtros por data
- [ ] Salvar preferências

### Relatórios
- [ ] Geração de relatórios PDF
- [ ] Exportação Excel
- [ ] Gráficos e análises
- [ ] Históricos

### Heatmap
- [ ] Heatmap de chuva
- [ ] Heatmap de ocorrências
- [ ] Heatmap de trânsito

---

## 9.  CONFIGURAÇÕES E DEPLOY

### Settings
- [ ] Configurar variáveis de ambiente
- [ ] Credenciais de APIs externas
- [ ] Configuração de banco produção
- [ ] CORS e segurança

### Deploy
- [ ] Configurar servidor
- [ ] nginx/Apache
- [ ] Gunicorn/uWSGI
- [ ] Supervisor/systemd
- [ ] SSL/HTTPS

---

## 10.  TESTES

- [ ] Testes unitários das views
- [ ] Testes das APIs
- [ ] Testes de integração
- [ ] Testes de carga
- [ ] Testes de interface

---

##  ESTIMATIVA DE TRABALHO

| Componente | Tempo Estimado |
|------------|----------------|
| Models e Migrations | 8-12 horas |
| Views/APIs (50 views) | 20-30 horas |
| Integrações APIs Externas | 15-20 horas |
| WebSocket Real-time | 6-8 horas |
| Navbar e Navegação | 4-6 horas |
| Funcionalidades Avançadas | 10-15 horas |
| Testes | 8-10 horas |
| Deploy e Configuração | 4-6 horas |
| **TOTAL** | **75-107 horas** |

---

##  PRIORIDADES SUGERIDAS

### FASE 1: Base (Essencial)
1.  Migrar Models críticos
2.  Criar migrations e popular banco
3.  Migrar 10-15 views principais

### FASE 2: Funcional (Importante)
1.  Integrações principais (Waze, Chuva, Sirenes)
2.  Navbar completa
3.  Sistema de filtros

### FASE 3: Avançado (Desejável)
1.  WebSocket real-time
2.  Dashboard completo
3.  Relatórios

### FASE 4: Polimento (Opcional)
1.  Testes completos
2.  Otimizações
3.  Deploy produção

