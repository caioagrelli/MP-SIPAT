# SIPAT — Sistema Integrado de Patrimônio e Almoxarifado

<div align="center">

> _[ logo / foto do Ministério Público aqui ]_

**Desenvolvido para o Ministério Público de Pernambuco**

</div>

---

## Sobre o Projeto

O **SIPAT** é um sistema web interno desenvolvido sob demanda para o **Ministério Público de Pernambuco (MPPE)**, mais especificamente para o **DEMPAM — Departamento de Material e Patrimônio**. O sistema nasceu da necessidade de digitalizar e centralizar processos que antes eram feitos manualmente ou em planilhas dispersas, sem rastreabilidade nem controle unificado.

O DEMPAM é o setor responsável por abastecer todas as Unidades Administrativas (UAs) do MPPE com materiais de consumo e por controlar o patrimônio permanente tombado da instituição. Com dezenas de UAs distribuídas pelo estado de Pernambuco, o volume de solicitações, movimentações e controles era inviável sem uma ferramenta adequada.

### O que o SIPAT resolve

- **Solicitações de materiais** — UAs solicitam bens de consumo diretamente pelo sistema. O DEMPAM recebe, analisa, separa e expede, com rastreamento em tempo real de cada etapa da tramitação.
- **Controle de estoque** — O estoque do almoxarifado é atualizado automaticamente conforme as solicitações avançam no fluxo, eliminando divergências entre o sistema e o estoque físico.
- **Gestão de contratos e saldo ativo** — Contratos com fornecedores são cadastrados com seus respectivos saldos. Solicitações podem ser vinculadas a contratos ativos, com baixa automática do saldo disponível.
- **Processo licitatório** — Artefatos de licitação (TR, ETP, RGPP, DODE, TAPP, Análise de Risco) são gerenciados dentro do sistema, com controle de estado e vinculação a propostas de fornecedores.
- **Patrimônio permanente** — Bens tombados são cadastrados com ficha completa (tombo, marca, modelo, valor, estado de conservação, situação física) e têm seu histórico de movimentação entre UAs registrado a cada transferência.
- **Rastreabilidade total** — Cada movimentação de bem permanente gera um registro imutável com origem, destino, responsável e data. O histórico de UAs por onde o bem passou fica preservado.
- **Uso externo** — Bens emprestados a servidores externos são registrados com responsável, CPF do usuário, contato e data de renovação.

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

| Tecnologia | Versão |
|---|---|
| Python | 3.14 |
| Django | 6.0.2 |
| Banco (dev) | SQLite |
| Banco (prod) | PostgreSQL |
| Autenticação | OIDC via Authentik |
| django-localflavor | 5.0 |
| Pillow | 12.1.0 |
| qrcode | 7.4.2 |

---

## Instalação

```bash
# Clone o repositório
git clone <url-do-repo>
cd sipat

# Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Instale as dependências
pip install -r requirements.txt

# Aplique as migrações
python manage.py migrate

# Crie o superusuário
python manage.py createsuperuser

# Rode o servidor
python manage.py runserver
```

---

## Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `DJANGO_SECRET_KEY` | Chave secreta do Django |
| `DJANGO_SETTINGS_MODULE` | Módulo de settings (`app.settings.development`) |
| `OIDC_RP_CLIENT_ID` | Client ID do Authentik |
| `OIDC_RP_CLIENT_SECRET` | Client Secret do Authentik |

---

## Estrutura do Projeto

```
sipat/
├── app/                    # Configuração central (settings, urls, wsgi)
│   └── settings/
│       ├── base.py
│       ├── development.py
│       └── production.py
├── dempam/                 # Estrutura base (UAs, prédios, localizações)
├── dimms/                  # Bens de consumo e almoxarifado
├── dimrcbp/                # Bens permanentes
├── static/                 # Arquivos estáticos (logo, ícones)
├── sipat.drawio            # Diagrama de entidades (draw.io)
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

## Autor

**Caio Agrelli** — Líder do projeto  
Desenvolvimento e gestão do SIPAT — MPPE/DEMPAM
