# Emulated Hue Manager — Home Assistant Add-on

Interface gráfica completa para gerenciamento da configuração do **Emulated Hue** do Home Assistant, eliminando a necessidade de edição manual do `configuration.yaml`.

---

## Funcionalidades

| Aba | Descrição |
|-----|-----------|
| **Dashboard** | Visão geral: totais, status, IP/porta, última modificação |
| **Configuração** | Editar `host_ip`, `listen_port`, `expose_by_default`, `upnp_bind_multicast`, `off_maps_to_on_domains`, `exposed_domains` |
| **Entidades** | CRUD completo com paginação server-side, busca, filtros combinados, duplicar, importar/exportar YAML |
| **Raw YAML** | Visualizar, editar, validar e salvar o bloco `emulated_hue` diretamente |
| **Backup / Restore** | Criar backups timestampados e restaurar via upload de arquivo `.yaml` |
| **Diagnóstico** | Verificar acessibilidade do endpoint UPnP (`/description.xml`) |
| **Auditoria** | Log de todas as ações realizadas (usuário, data, ação, alvo) |

---

## Arquitetura

```
addon/
├── rootfs/
│   └── app/
│       ├── api/
│       │   ├── dependencies.py        # Injeção de dependência (lru_cache)
│       │   └── routes/
│       │       ├── audit.py
│       │       ├── backup.py
│       │       ├── config.py
│       │       ├── dashboard.py
│       │       ├── diagnostics.py
│       │       ├── entities.py
│       │       └── reload.py
│       ├── models/                    # Modelos de domínio (dataclasses)
│       │   ├── audit.py
│       │   ├── config.py
│       │   └── entity.py
│       ├── repositories/              # Repository Pattern — acesso ao YAML
│       │   └── yaml_repository.py
│       ├── schemas/                   # Pydantic DTOs (request/response)
│       │   ├── common.py
│       │   ├── config.py
│       │   └── entity.py
│       ├── services/                  # Camada de aplicação
│       │   ├── backup_service.py
│       │   ├── config_service.py
│       │   ├── diagnostics_service.py
│       │   ├── entity_service.py
│       │   └── ha_service.py
│       ├── utils/
│       │   ├── audit.py               # Audit logger (JSONL)
│       │   ├── logger.py              # Logger estruturado
│       │   └── yaml_utils.py          # Utilitários YAML seguros
│       ├── frontend/                  # SPA em Vanilla JS + ES Modules
│       │   ├── index.html
│       │   ├── app.js
│       │   ├── components/
│       │   └── styles/
│       └── main.py                    # FastAPI app
├── config.yaml                        # Configuração do Add-on HA
├── build.yaml                         # Build multi-arch
├── Dockerfile
└── requirements.txt

tests/
├── conftest.py
├── unit/
│   ├── test_config_service.py
│   ├── test_entity_service.py
│   └── test_yaml_repository.py
└── integration/
    └── test_api.py
```

### Princípios Aplicados

- **SOLID** — cada classe tem responsabilidade única, extensível via interfaces/protocolos
- **Clean Architecture** — domínio isolado, infraestrutura injetada
- **Arquitetura Hexagonal** — ports (interfaces de serviço) e adapters (YAML repository, HA API)
- **Repository Pattern** — `YamlConfigRepository` é o único ponto de acesso à persistência
- **Service Layer** — `ConfigService`, `EntityService`, `BackupService` orquestram as regras
- **DTOs** — schemas Pydantic separados de models de domínio
- **Dependency Injection** — via `lru_cache` no módulo `dependencies.py`
- **Auditoria** — todas as mutações são registradas em JSONL com usuário/ação/alvo

---

## APIs

```
GET    /api/dashboard
GET    /api/config
PUT    /api/config
GET    /api/config/yaml
PUT    /api/config/yaml
GET    /api/entities
GET    /api/entities/{entity_id}
POST   /api/entities
PUT    /api/entities/{entity_id}
DELETE /api/entities/{entity_id}
GET    /api/entities/export
POST   /api/entities/import
POST   /api/entities/duplicate?source_id=&new_id=
POST   /api/reload
POST   /api/backup
GET    /api/backup/list
POST   /api/backup/restore
GET    /api/diagnostics
GET    /api/audit
```

Documentação interativa disponível em `/api/docs` (Swagger UI).

---

## Instalação via Repositório Customizado

1. No Home Assistant, acesse **Configurações → Add-ons → Loja de Add-ons**
2. Clique nos **três pontos** (canto superior direito) → **Repositórios**
3. Adicione a URL do repositório:
   ```
   https://github.com/grassato/ha_emuleted_hue_admin
   ```
4. Procure por **"Emulated Hue Manager"** e clique em **Instalar**
5. Habilite **Ingress** e inicie o Add-on

---

## Desenvolvimento Local

### Pré-requisitos
- Python 3.13+
- pip

### Setup

```bash
cd ha_emuleted_hue_admin

# Instalar dependências
pip install -e ".[dev]"

# Rodar servidor local (apontando para um configuration.yaml de teste)
export HA_CONFIG_PATH="./tests/fixtures/configuration.yaml"
uvicorn addon.rootfs.app.main:app --reload --port 8099
```

### Testes

```bash
# Testes unitários e de integração
pytest

# Com cobertura
pytest --cov --cov-report=term-missing

# Apenas unitários
pytest tests/unit/

# Apenas integração
pytest tests/integration/
```

---

## Segurança

- Leitura e escrita YAML via operações atômicas (arquivo `.tmp` + rename)
- Backup automático antes de qualquer mutação
- Validação de YAML antes de persistir
- Limite de 5MB no upload de restore
- Sem SQL, sem execução de código externo
- Secrets via variáveis de ambiente (`SUPERVISOR_TOKEN`)

---

## Licença

MIT © Diego Grassato
