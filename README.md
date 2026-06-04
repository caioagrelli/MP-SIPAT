# SIPAT — Sistema Integrado Patrimonial

<div align="center">

<img src="static/img/brasao-mppe.png" alt="Brasão MPPE" width="120"/>

**Desenvolvido para o Ministério Público de Pernambuco**

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0.2-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/Licença-MIT-green)

</div>

---

## Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Screenshots](#screenshots)
- [Módulos](#módulos)
- [Stack](#stack)
- [Instalação](#instalação)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Rodando com Docker](#rodando-com-docker)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Diagramas](#diagramas)
- [Contribuindo](#contribuindo)
- [Autor](#autor)

---

## Sobre o Projeto

O **SIPAT** é um sistema web interno desenvolvido sob demanda para o **Ministério Público de Pernambuco (MPPE)**, mais especificamente para o **DEMPAM — Departamento de Material e Patrimônio**. O sistema nasceu da necessidade de digitalizar e centralizar processos que antes eram feitos manualmente ou em planilhas dispersas, sem rastreabilidade nem controle unificado.

O DEMPAM é o setor responsável por abastecer todas as Unidades Administrativas (UAs) do MPPE com materiais de consumo e por controlar o patrimônio permanente tombado da instituição. Com dezenas de UAs distribuídas pelo estado de Pernambuco, o volume de solicitações, movimentações e controles era inviável sem uma ferramenta adequada.

### O que o SIPAT resolve

| Funcionalidade | Descrição |
|---|---|
| **Solicitações de materiais** | UAs solicitam bens de consumo diretamente pelo sistema. O DEMPAM recebe, analisa, separa e expede, com rastreamento em tempo real de cada etapa da tramitação. |
| **Controle de estoque** | O estoque do almoxarifado é atualizado automaticamente conforme as solicitações avançam no fluxo, eliminando divergências entre o sistema e o estoque físico. |
| **Gestão de contratos** | Contratos com fornecedores são cadastrados com seus respectivos saldos. Solicitações podem ser vinculadas a contratos ativos, com baixa automática do saldo disponível. |
| **Processo licitatório** | Artefatos de licitação (TR, ETP, RGPP, DODE, TAPP, Análise de Risco) são gerenciados dentro do sistema, com controle de estado e vinculação a propostas de fornecedores. |
| **Patrimônio permanente** | Bens tombados são cadastrados com ficha completa (tombo, marca, modelo, valor, estado de conservação, situação física) e têm seu histórico de movimentação entre UAs registrado a cada transferência. |
| **Rastreabilidade total** | Cada movimentação de bem permanente gera um registro imutável com origem, destino, responsável e data. O histórico de UAs por onde o bem passou fica preservado. |
| **Uso externo** | Bens emprestados a servidores externos são registrados com responsável, CPF do usuário, contato e data de renovação. |

### Contexto institucional

O sistema foi entregue ao **MPPE/DEMPAM** e está em uso interno. Todo o ciclo de desenvolvimento foi conduzido pelo autor — desde o levantamento de requisitos com o setor, passando pela modelagem do banco de dados, desenvolvimento de cada módulo, até a implantação e manutenção evolutiva do sistema.

---

## Screenshots

### Homepage

> _[ insira screenshot aqui ]_

---

### DIMMS — Almoxarifado

> _[ insira screenshot aqui ]_

---

### DIMRCBP — Bens Permanentes

> _[ insira screenshot aqui ]_

---

### DEMPAM — Painel Gerencial

> _[ insira screenshot aqui ]_

---

### Admin

> _[ insira screenshot aqui ]_

---

## Módulos

### `dempam` — Estrutura Base

Cadastros centrais compartilhados pelos demais módulos.

| Model | Descrição |
|---|---|
| `CircunscricaoPredio` | Prédios e circunscrições geográficas |
| `InfoUA` | Unidades Administrativas (responsável, contato, sede) |
| `SetorDEMPAM` | Setores e salas internas do DEMPAM |
| `LocalizacaoDEMPAM` | Localizações físicas (prateleiras, pallets) |

---

### `dimms` — Bens de Consumo

Controla o ciclo completo dos bens de consumo: do estoque à entrega.

| Model | Descrição |
|---|---|
| `BensConsumo` | Catálogo de itens (E-Fisco) |
| `Supplier` | Fornecedores |
| `Contrato` | Contratos com fornecedores |
| `SaldoAtivo` | Saldo de itens por contrato |
| `Estoque` | Estoque físico do DEMPAM |
| `Solicitacao` | Solicitações de materiais pelas UAs (`SBC-YYYY-XXXX`) |
| `SolicitacaoItens` | Itens de cada solicitação |
| `Tramitacao` | Histórico de tramitação — baixa o estoque automaticamente |
| `BensEnviados` | Registro dos itens efetivamente enviados |
| `SolicitacoesSaldoAtivo` | Solicitações via saldo de contrato (`SSA-YYYY-XXXX`) |
| `ItensSolicitados` | Itens das solicitações de saldo ativo |
| `Artifacts` | Artefatos de licitação (TR, ETP, RGPP, DODE, TAPP) |
| `ItensArtifacts` | Itens vinculados a artefatos |
| `Proposal` | Propostas de fornecedores |
| `ItensProposal` | Itens de cada proposta |

**Fluxo de solicitação:**
```
UA cria Solicitação → adiciona Itens → Tramitação
Em Atendimento → Aguardando Separação → Separada → Em Expedição → Recebida
                                ↑
                    Estoque baixado automaticamente
```

---

### `dimrcbp` — Bens Permanentes

Controla o patrimônio permanente tombado.

| Model | Descrição |
|---|---|
| `Groups` | Grupos de bens permanentes |
| `Type` | Tipos de bens (vinculado ao grupo) |
| `Description` | Descrição detalhada (cor, tamanho, BTU/HP) |
| `Supplier` | Fornecedores de bens permanentes |
| `BensPermanentes` | Bens tombados (tombo, marca, modelo, valor) |
| `HistoryUas` | Histórico de UAs por onde o bem passou |
| `UseExternal` | Registro de uso externo do bem |
| `MovimentacoesPermanentes` | Movimentações entre UAs (transferência, devolução) |

---

## Stack

| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.14 | Linguagem principal |
| Django | 6.0.2 | Framework web |
| PostgreSQL | 16 | Banco de dados (produção) |
| SQLite | — | Banco de dados (desenvolvimento) |
| Authentik (OIDC) | — | Autenticação institucional |
| Gunicorn | 23.0.0 | Servidor WSGI |
| WhiteNoise | 6.9.0 | Arquivos estáticos |
| django-localflavor | 5.0 | Validações brasileiras (CPF, CNPJ) |
| Pillow | 12.1.0 | Processamento de imagens |
| qrcode | 7.4.2 | Geração de QR Code para bens |
| ReportLab | 4.0.9 | Geração de PDFs |
| openpyxl | 3.1.5 | Importação/exportação de planilhas |

---

## Instalação

### Desenvolvimento local (SQLite)

```bash
# Clone o repositório
git clone <url-do-repo>
cd sipat

# Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# Instale as dependências
pip install -r requirements.txt

# Aplique as migrações
python manage.py migrate

# Crie o superusuário
python manage.py createsuperuser

# Rode o servidor
python manage.py runserver
```

Acesse em `http://localhost:8000`.

---

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

| Variável | Descrição |
|---|---|
| `DJANGO_SECRET_KEY` | Chave secreta do Django |
| `DJANGO_SETTINGS_MODULE` | Módulo de settings (ex.: `app.settings.development`) |
| `DB_NAME` | Nome do banco PostgreSQL |
| `DB_USER` | Usuário do banco PostgreSQL |
| `DB_PASSWORD` | Senha do banco PostgreSQL |
| `OIDC_RP_CLIENT_ID` | Client ID do Authentik |
| `OIDC_RP_CLIENT_SECRET` | Client Secret do Authentik |

---

## Rodando com Docker

Para usar PostgreSQL localmente com Docker:

```bash
docker compose up
```

O Docker Compose sobe dois serviços:

- **`db`** — PostgreSQL 16 com healthcheck
- **`web`** — Django + Gunicorn, executa migrações e collectstatic automaticamente na inicialização

Certifique-se de que o `.env` contém as variáveis `DB_NAME`, `DB_USER` e `DB_PASSWORD`.

---

## Estrutura do Projeto

```
sipat/
├── app/                    # Configuração central (settings, urls, wsgi)
│   └── settings/
│       ├── base.py
│       ├── development.py
│       ├── local.py
│       ├── staging.py
│       └── production.py
├── dempam/                 # Estrutura base (UAs, prédios, localizações)
├── dimms/                  # Bens de consumo e almoxarifado
├── dimrcbp/                # Bens permanentes
├── templates/              # Templates HTML
├── static/                 # Arquivos estáticos (logo, ícones)
├── docs/                   # Documentação adicional
├── sipat.drawio            # Diagrama de entidades (draw.io)
├── docker-compose.yml
└── requirements.txt
```

---

## Diagramas

O arquivo `sipat.drawio` contém os diagramas de entidade-relacionamento do sistema, organizado por páginas:

- **contract** — Fluxo de contratos e fornecedores
- **DIMMS** — Estrutura de bens de consumo
- **DIMRCBP** — Estrutura de bens permanentes
- **DEMPAM** — Estrutura base (UAs e localizações)

---

## Contribuindo

Consulte os documentos abaixo antes de contribuir:

- [CONTRIBUTING.md](CONTRIBUTING.md) — como configurar o ambiente, convenções de commits e fluxo de PRs
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — padrões de comportamento esperados
- [SECURITY.md](SECURITY.md) — como reportar vulnerabilidades

---

## Autor

**Caio Agrelli** — Engenheiro de Software Responsável
Desenvolvimento e gestão do SIPAT — MPPE/DEMPAM
