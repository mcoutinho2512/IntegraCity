# IntegraCity - Sistema Integrado de Monitoramento Urbano

Sistema de monitoramento e gestão de operações urbanas desenvolvido para centros de operações municipais. Integra múltiplas fontes de dados em tempo real para apoio à tomada de decisão.

---

## Visão Geral

O **IntegraCity** é uma plataforma web completa para monitoramento urbano que centraliza informações de diversas fontes:

- **Videomonitoramento** - Câmeras de segurança em tempo real
- **Meteorologia** - Dados climáticos e alertas do INMET
- **Mobilidade** - Trânsito e alertas do Waze
- **Ocorrências** - Gestão de eventos e incidentes
- **Áreas de Observação** - Monitoramento geográfico com alertas
- **Matriz Decisória** - Motor automático de estágios operacionais

---

## Tecnologias

### Backend
- **Python 3.10+**
- **Django 5.1** - Framework web
- **Django REST Framework** - APIs REST
- **Celery** - Tarefas assíncronas
- **Redis** - Cache e message broker
- **SQLite/PostgreSQL** - Banco de dados

### Frontend
- **HTML5/CSS3/JavaScript**
- **Leaflet.js** - Mapas interativos
- **Bootstrap Icons** - Iconografia
- **Design System Hightech** - Interface moderna

### Integrações Externas
- **TIXXI** - Videomonitoramento e câmeras
- **Waze** - Dados de trânsito e alertas
- **INMET** - Estações meteorológicas
- **ViaCEP** - Consulta de endereços

---

## Estrutura do Projeto

```
integracity/
├── aplicativo/                 # Aplicação Django principal
│   ├── models.py              # Modelos de dados
│   ├── views.py               # Views principais
│   ├── views_areas.py         # Áreas de observação
│   ├── views_matriz.py        # Matriz decisória
│   ├── views_meteorologia.py  # Meteorologia
│   ├── views_mobilidade.py    # Mobilidade/Waze
│   ├── views_ocorrencias.py   # Gestão de ocorrências
│   ├── views_users.py         # Gestão de usuários
│   ├── urls.py                # Rotas da aplicação
│   ├── middleware.py          # Middlewares customizados
│   ├── templates/             # Templates HTML
│   │   ├── base_hightech.html
│   │   ├── cor_dashboard_hightech.html
│   │   ├── videomonitoramento_hightech.html
│   │   ├── areas/
│   │   ├── matriz/
│   │   ├── meteorologia/
│   │   ├── mobilidade/
│   │   ├── ocorrencias/
│   │   └── users/
│   └── services/              # Serviços externos
├── sitecor/                   # Configurações Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── static/                    # Arquivos estáticos
│   ├── css/
│   ├── js/
│   │   └── cameras_thumbnails.js
│   └── images/
├── staticfiles/               # Arquivos coletados (produção)
├── logs/                      # Logs da aplicação
├── .env                       # Variáveis de ambiente
├── requirements.txt           # Dependências Python
└── manage.py                  # CLI Django
```

---

## Módulos do Sistema

### 1. Dashboard Principal
- Mapa interativo com camadas sobrepostas
- Indicadores em tempo real
- Estágio operacional atual
- Alertas e notificações

### 2. Videomonitoramento
- Grid de câmeras com thumbnails ao vivo
- Player modal responsivo
- Paginação configurável (5 câmeras/página)
- Integração TIXXI com imagem direta
- Indicador de status online/offline

**Endpoint de streaming:**
```
/api/camera/<camera_id>/stream/?embed=1
```

### 3. Meteorologia
- Estações meteorológicas INMET
- Dados de temperatura, umidade, vento
- Índice de calor
- Alertas automáticos por thresholds

### 4. Mobilidade (Waze)
- Mapa de trânsito em tempo real
- Alertas categorizados (acidentes, obras, etc.)
- Vias engarrafadas
- Nível de congestionamento

### 5. Ocorrências
- Cadastro e gestão de incidentes
- Workflow de status
- Acionamento de agências
- POPs (Procedimentos Operacionais)
- Histórico e comentários

### 6. Áreas de Observação
- Desenho de polígonos no mapa
- Importação KML/KMZ
- Inventário automático de recursos
- Alertas por entrada em área
- Exportação GeoJSON/KML/PDF

### 7. Matriz Decisória
- Cálculo automático de estágios
- Parâmetros configuráveis
- Histórico de decisões
- Gráficos e estatísticas

### 8. Gestão de Usuários
- Autenticação segura
- Níveis de permissão
- Logs de auditoria
- Bloqueio por tentativas

---

## Instalação

### Pré-requisitos
- Python 3.10+
- pip
- virtualenv
- Redis (opcional, para Celery)

### Passos

1. **Clonar o repositório**
```bash
git clone https://github.com/mcoutinho2512/IntegraCity.git
cd integracity
```

2. **Criar ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Instalar dependências**
```bash
pip install -r requirements.txt
```

4. **Configurar variáveis de ambiente**
```bash
cp .env.example .env
# Editar .env com suas configurações
```

5. **Executar migrações**
```bash
python manage.py migrate
```

6. **Coletar arquivos estáticos**
```bash
python manage.py collectstatic --noinput
```

7. **Criar superusuário**
```bash
python manage.py createsuperuser
```

8. **Executar servidor**
```bash
# Desenvolvimento
python manage.py runserver

# Produção (com gunicorn)
gunicorn sitecor.wsgi:application --bind 127.0.0.1:8890 --workers 2 --reload
```

---

## Configuração (.env)

```env
# Django
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=seu-dominio.com,localhost,127.0.0.1
SECRET_KEY=sua-chave-secreta

# TIXXI (Videomonitoramento)
TIXXI_BASE_URL=https://dev.tixxi.rio
TIXXI_VIDEO_KEY=sua-chave
TIXXI_VIDEO_ENDPOINT=outvideo2
TIXXI_AUTH_URL=https://tixxi.rio/tixxi/api/cora/auth.php
TIXXI_USER=usuario
TIXXI_PASS=senha

# Banco de Dados (se PostgreSQL)
DATABASE_URL=postgres://user:pass@localhost:5432/integracity
```

---

## APIs Disponíveis

### Câmeras
| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/cameras/` | GET | Lista todas as câmeras |
| `/api/camera/<id>/stream/` | GET | Stream de vídeo |
| `/api/camera/<id>/snapshot/` | GET | Snapshot da câmera |
| `/api/cameras/status/` | GET | Status das câmeras |

### Meteorologia
| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/meteo/coletar/` | POST | Coletar dados INMET |
| `/api/meteo/estacao/<codigo>/` | GET | Dados de estação |
| `/api/meteo/nivel/` | GET | Nível meteorológico |
| `/api/meteo/calor/` | GET | Índice de calor |

### Mobilidade
| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/mob/dados/` | GET | Dados de mobilidade |
| `/api/mob/jams/` | GET | Engarrafamentos |
| `/api/mob/alerts/` | GET | Alertas Waze |
| `/api/mob/nivel/` | GET | Nível de trânsito |

### Ocorrências
| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/ocorrencias/mapa/` | GET | Ocorrências no mapa |
| `/api/ocorrencias/estatisticas/` | GET | Estatísticas |
| `/api/cep/` | GET | Busca CEP |

### Áreas
| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/areas/listar/` | GET | Listar áreas |
| `/api/areas/criar/` | POST | Criar área |
| `/api/areas/<id>/inventariar/` | GET | Inventário |
| `/api/areas/<id>/alertas/` | GET | Alertas da área |
| `/api/areas/importar-kml/` | POST | Importar KML/KMZ |

### Matriz Decisória
| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/matriz/calcular/` | POST | Calcular estágio |
| `/api/matriz/ultimo/` | GET | Último estágio |
| `/api/matriz/historico/` | GET | Histórico |

---

## Deploy em Produção

### Nginx (exemplo de configuração)

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location /integracity/ {
        proxy_pass http://127.0.0.1:8890/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /integracity/static/ {
        alias /home/administrador/integracity/staticfiles/;
    }
}
```

### Systemd Service

```ini
[Unit]
Description=IntegraCity Gunicorn
After=network.target

[Service]
User=administrador
Group=administrador
WorkingDirectory=/home/administrador/integracity
ExecStart=/home/administrador/integracity/venv/bin/gunicorn \
    sitecor.wsgi:application \
    --bind 127.0.0.1:8890 \
    --workers 2 \
    --reload

[Install]
WantedBy=multi-user.target
```

---

## Segurança

- Autenticação obrigatória (exceto APIs públicas configuradas)
- Proteção CSRF em formulários
- Sanitização de inputs
- Logs de auditoria
- Bloqueio por tentativas de login
- Chaves de API no backend (não expostas ao frontend)

### URLs Públicas (sem autenticação)
Configuradas em `aplicativo/middleware.py`:
- `/api/estagio/`
- `/api/alertas/`
- `/api/camera/`

---

## Manutenção

### Logs
```bash
tail -f /home/administrador/integracity/logs/integracity.log
```

### Restart do serviço
```bash
sudo systemctl restart integracity
# ou
touch sitecor/wsgi.py  # Se usando --reload
```

### Backup do banco
```bash
cp db.sqlite3 backups/db_$(date +%Y%m%d_%H%M%S).sqlite3
```

### Atualizar código
```bash
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
touch sitecor/wsgi.py
```

---

## Contribuição

1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Add nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

---

## Licença

Este projeto é proprietário e de uso restrito.

---

## Contato

- **Repositório:** https://github.com/mcoutinho2512/IntegraCity
- **Desenvolvido para:** Centro de Operações Rio

---

*Última atualização: Janeiro 2026*
