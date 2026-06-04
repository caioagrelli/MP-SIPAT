# Arquitetura do SIPAT — Modelo C4

> Documentação arquitetural nos 4 níveis do modelo C4 (Context, Container, Component, Code).

---

## Nível 1 — Contexto do Sistema

Visão macro: quem usa o SIPAT e com quais sistemas externos ele se comunica.

```mermaid
graph TB
    subgraph Usuarios["Usuários"]
        UA_MEMBER["👤 Membro de UA\nServidor público que solicita\nmateriais e gerencia bens"]
        UA_GESTOR["👤 Gestor de UA\nApova solicitações e\ngerencia a sua unidade"]
        DEMPAM_OP["👤 Operador DEMPAM\nGestão de estoque, contratos,\nbens permanentes e licitações"]
        ADMIN["👤 Administrador\nGestão de usuários,\npermissões e configurações"]
    end

    subgraph SIPAT["SIPAT — Sistema Integrado de Patrimônio e Almoxarifado"]
        APP["🖥️ Aplicação Web\nDjango 6 · Python 3.14"]
    end

    subgraph Externos["Sistemas Externos"]
        AUTHENTIK["🔐 Authentik\nProvedor de identidade\nOpenID Connect · SSO institucional"]
        POSTGRES["🗄️ PostgreSQL 16\nBanco de dados relacional\nAmbiente de produção"]
        EMAIL["📧 Servidor de E-mail\nReset de senha via\nDjango password reset"]
    end

    UA_MEMBER -->|"Solicita materiais\nGerencia bens atribuídos"| APP
    UA_GESTOR -->|"Aprova solicitações\nGerencia UA"| APP
    DEMPAM_OP -->|"Gestão operacional\nEstoque · Patrimônio"| APP
    ADMIN -->|"Gestão de usuários\ne permissões"| APP

    APP -->|"Autenticação SSO\nOIDC + PKCE + RS256"| AUTHENTIK
    APP -->|"Leitura e escrita\nde dados"| POSTGRES
    APP -->|"Envio de e-mail\npara reset de senha"| EMAIL
```

---

## Nível 2 — Containers

Visão das peças tecnológicas que compõem o sistema e como se comunicam.

```mermaid
graph TB
    BROWSER["🌐 Navegador\nHTML · CSS · JS vanilla\nDjango Templates"]

    subgraph SIPAT["SIPAT (Docker Compose)"]
        DJANGO["⚙️ Django Application\nGunicorn · Python 3.14\nPorta 8000\n\nResponsável por toda a lógica\nde negócio, renderização de\ntemplates e API interna"]

        STATIC["📁 Arquivos Estáticos\nWhiteNoise\n\nCSS · JS · Imagens\nservidos pelo próprio Django\nem produção"]

        MEDIA["📁 Arquivos de Mídia\nVolume Docker\n\nFotos de bens permanentes\ne itens de estoque"]
    end

    subgraph Infra["Infraestrutura"]
        POSTGRES["🗄️ PostgreSQL 16\nVolume Docker\n\nTodos os dados\ntransacionais do sistema"]
    end

    subgraph Ext["Externos"]
        AUTHENTIK["🔐 Authentik\nSSO · OIDC\n\nProvedor de identidade\ninstitucional do MPPE"]
        EMAIL["📧 SMTP\nReset de senha"]
    end

    BROWSER -->|"HTTPS · Requisições HTTP\nFormulários · Navegação"| DJANGO
    BROWSER -->|"Arquivos estáticos\n(CSS, JS, imagens)"| STATIC

    DJANGO -->|"ORM Django\npsycopg 3"| POSTGRES
    DJANGO -->|"Serve em produção\n(WhiteNoise)"| STATIC
    DJANGO -->|"Leitura e escrita\nde arquivos"| MEDIA
    DJANGO -->|"Redirect OIDC\nTroca de token\nValidação JWT RS256"| AUTHENTIK
    DJANGO -->|"SMTP\nDjango email backend"| EMAIL
```

---

## Nível 3 — Componentes

Visão interna da aplicação Django: seus módulos (apps) e as responsabilidades de cada um.

```mermaid
graph TB
    BROWSER["🌐 Navegador"]

    subgraph APP["Django Application"]
        CORE["🔧 app/\nRoteamento central\nSettings por ambiente\nURLs raiz\nOIDC callback"]

        subgraph APPS["Apps de Negócio"]
            ACCOUNTS["👥 accounts\n─────────────\nUsuários e perfis\nGrupos e permissões\nVinculação a UAs\nDecorador @management_required"]

            DEMPAM["🏛️ dempam\n─────────────\nUnidades Administrativas\nPrédios e Circunscrições\nSetores e Localizações\nHomepage e roteamento base"]

            DEMANDS["📋 demands\n─────────────\nDemandas e tickets\nAtribuição a usuários\nHistórico e comentários\nTipos configuráveis"]

            DIMMS["📦 dimms\n─────────────\nEstoque de consumo\nSolicitações de materiais\nContratos e saldo ativo\nArtefatos de licitação\nCatálogo de consumo"]

            DIMRCBP["🏷️ dimrcbp\n─────────────\nBens permanentes\nMovimentações entre UAs\nInventário periódico\nCatálogo de patrimônio\nTermos de transferência"]
        end
    end

    BROWSER -->|"HTTP"| CORE
    CORE --> ACCOUNTS
    CORE --> DEMPAM
    CORE --> DEMANDS
    CORE --> DIMMS
    CORE --> DIMRCBP

    ACCOUNTS -->|"InfoUA (UAs do usuário)"| DEMPAM
    DEMANDS -->|"InfoUA (UA da demanda)"| DEMPAM
    DIMMS -->|"InfoUA (UA solicitante)\nLocalizacaoDEMPAM (estoque)"| DEMPAM
    DIMRCBP -->|"InfoUA (UA do bem)\nMovimentação entre UAs"| DEMPAM
```

---

## Nível 4 — Código

### `accounts` — Gestão de Acesso

```mermaid
erDiagram
    User ||--o| Profile : "1:1"
    Profile }o--o{ InfoUA : "uas (M:M)"
    Profile }o--o{ InfoUA : "managed_uas (M:M)"
    User }o--o{ Group : "M:M"

    Profile {
        int user
        image photo
        string phone
        string bio
    }
```

---

### `dempam` — Estrutura Organizacional

```mermaid
erDiagram
    CircunscricaoPredio ||--o{ InfoUA : "prédio da UA"
    User ||--o{ InfoUA : "gestor"
    InfoUA ||--o{ SetorDEMPAM : "setores internos"
    SetorDEMPAM ||--o{ LocalizacaoDEMPAM : "localizações"

    CircunscricaoPredio {
        string local
        string meso
        string micro
    }
    InfoUA {
        string ua
        string responsavel_ua
        string mat_resp_ua
        string email_ua
        string contato_ua
        string sede
    }
    SetorDEMPAM {
        string setor
    }
    LocalizacaoDEMPAM {
        string setor_sala
        string prateleira_pallet
        string tipo_localizacao
    }
```

---

### `demands` — Demandas e Tickets

```mermaid
erDiagram
    DemandType ||--o{ Demand : "tipo"
    DemandType }o--o{ Group : "grupos permitidos"
    InfoUA ||--o{ Demand : "UA da demanda"
    User ||--o{ Demand : "criador"
    Demand ||--o{ DemandAssignment : "atribuições"
    User ||--o{ DemandAssignment : "atribuído"
    Demand ||--o{ DemandAttachment : "anexos"
    Demand ||--o{ DemandUpdate : "histórico"

    DemandType {
        string name
        string color
        string icon
        bool is_active
    }
    Demand {
        string code
        string title
        string description
        enum priority
        enum status
        date deadline
    }
    DemandAssignment {
        bool can_change_status
    }
    DemandUpdate {
        string comment
        string status_change
        file file
    }
```

---

### `dimms` — Bens de Consumo

```mermaid
erDiagram
    BensConsumo ||--o{ Estoque : "item no estoque"
    LocalizacaoDEMPAM ||--o{ Estoque : "localização"
    Estoque ||--o{ SolicitacaoItem : "itens solicitados"
    Solicitacao ||--o{ SolicitacaoItem : "itens"
    InfoUA ||--o{ Solicitacao : "UA solicitante"

    Supplier ||--o{ Contrato : "contrato"
    Contrato ||--o{ SaldoAtivo : "saldo"
    BensConsumo ||--o{ SaldoAtivo : "item do saldo"

    Supplier ||--o{ Artifacts : "fornecedor"
    Artifacts ||--o{ Proposal : "propostas"
    Supplier ||--o{ Proposal : "fornecedor"

    BensConsumo ||--o| CatalogoConsumo : "catálogo"
    CatalogoConsumo ||--o{ ItemSolicitacaoCatalogoConsumo : "itens"
    SolicitacaoCatalogoConsumo ||--o{ ItemSolicitacaoCatalogoConsumo : "solicitação"
    InfoUA ||--o{ SolicitacaoCatalogoConsumo : "UA destino"
    User ||--o{ SolicitacaoCatalogoConsumo : "solicitante"

    Solicitacao {
        string request_code
        enum situation
        bool stock_deducted
    }
    Estoque {
        int amount_shock
        bool essential
        date validity
        int monthly_consumption
    }
    Contrato {
        date inicio_vigencia
        date final_vigencia
        enum status
    }
    SaldoAtivo {
        int quantidade_contrato
        int saldo_disponivel
        enum cota
    }
```

---

### `dimrcbp` — Bens Permanentes

```mermaid
erDiagram
    Groups ||--o{ Type : "tipos"
    Type ||--o{ Description : "descrições"
    Description ||--o{ BensPermanentes : "bem"
    Supplier ||--o{ BensPermanentes : "fornecedor"

    BensPermanentes ||--o| HistoryUas : "UA atual (1:1)"
    InfoUA ||--o{ HistoryUas : "UA"

    BensPermanentes ||--o{ AtribuicaoBem : "atribuições"
    User ||--o{ AtribuicaoBem : "responsável"
    InfoUA ||--o{ AtribuicaoBem : "UA"

    BensPermanentes ||--o{ MovimentacaoBem : "movimentações"
    InfoUA ||--o{ MovimentacaoBem : "UA origem"
    InfoUA ||--o{ MovimentacaoBem : "UA destino"
    User ||--o{ MovimentacaoBem : "executou"

    BensPermanentes ||--o{ HistoricoMudanca : "audit trail"
    BensPermanentes ||--o{ Inventario : "inventários"
    PeriodoInventario ||--o{ Inventario : "período"

    BensPermanentes {
        string tombo
        string mark
        string model
        decimal value
        enum state
        enum situacion
        string entry_method
    }
    MovimentacaoBem {
        enum tipo_movimentacao
        date data_movimentacao
        string justificativa
    }
    Inventario {
        enum situacao
        date data_verificacao
    }
```

---

## Fluxos Principais

### Autenticação

```mermaid
sequenceDiagram
    actor U as Usuário
    participant B as Navegador
    participant D as Django
    participant A as Authentik (OIDC)

    U->>B: Acessa /home/
    B->>D: GET /home/
    D->>B: Redirect → /oidc/authenticate/
    B->>A: Authorization Request (PKCE · RS256)
    A->>U: Tela de login institucional
    U->>A: Credenciais MPPE
    A->>B: Redirect com authorization_code
    B->>D: GET /oidc/callback/?code=...
    D->>A: Troca code por access_token + id_token
    A->>D: Tokens JWT (RS256)
    D->>D: Valida token · Carrega/cria User
    D->>B: Redirect → /home/ (sessão criada)
    B->>U: Dashboard SIPAT
```

---

### Solicitação de Material (DIMMS)

```mermaid
sequenceDiagram
    actor M as Membro UA
    actor G as Gestor UA / DEMPAM
    participant S as SIPAT

    M->>S: Acessa catálogo de consumo
    S->>M: Lista itens disponíveis (CatalogoConsumo)
    M->>S: Cria solicitação com itens + quantidades
    S->>S: Cria SolicitacaoCatalogoConsumo (PENDENTE)
    S->>G: Solicitação aparece no painel de aprovação
    G->>S: Aprova solicitação
    S->>S: Baixa estoque automaticamente
    S->>S: Atualiza status → APROVADA
    G->>S: Marca como ENTREGUE após expedição
    S->>M: Solicitação concluída
```

---

### Transferência de Bem Permanente (DIMRCBP)

```mermaid
sequenceDiagram
    actor O as Operador DEMPAM
    participant S as SIPAT
    actor G as Gestor UA Destino

    O->>S: Cria SolicitacaoTransferencia (bem + UA destino)
    S->>G: Solicitação visível para aprovação
    G->>S: Aprova transferência
    S->>S: Cria MovimentacaoBem (origem → destino)
    S->>S: Atualiza HistoryUas (nova UA atual)
    S->>S: Registra HistoricoMudanca (audit trail)
    S->>O: Gera Termo de Transferência (PDF · ReportLab)
    O->>S: Arquiva termo assinado
```

---

## Ambientes

| Ambiente | Settings | Banco | Autenticação | Obs. |
|---|---|---|---|---|
| `development` | `app.settings.development` | SQLite | Django auth (form) | Padrão para devs |
| `local` | `app.settings.local` | PostgreSQL (Docker) | Django auth (form) | Docker Compose local |
| `staging` | `app.settings.staging` | PostgreSQL | OIDC (Authentik) | Homologação |
| `production` | `app.settings.production` | PostgreSQL | OIDC (Authentik) | MPPE produção |
