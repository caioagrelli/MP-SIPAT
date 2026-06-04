# CLAUDE.md — SIPAT

Guia de referência rápida para trabalhar neste repositório.

---

## Comandos essenciais

```bash
# Ambiente de desenvolvimento (SQLite)
python manage.py runserver                          # inicia o servidor
python manage.py migrate                            # aplica migrações
python manage.py makemigrations                     # gera migrações
python manage.py createsuperuser                    # cria superusuário
python manage.py shell                              # shell Django

# Ambiente local com PostgreSQL (Docker)
docker compose up                                   # sobe db + web
docker compose up db                               # sobe só o banco

# Testes
python manage.py test                               # roda todos os testes
python manage.py test dimms                         # testa app específico
```

Variável de ambiente obrigatória para rodar localmente:

```bash
export DJANGO_SETTINGS_MODULE=app.settings.development   # SQLite
export DJANGO_SETTINGS_MODULE=app.settings.local         # PostgreSQL local
```

---

## Estrutura dos apps

| App | Namespace de URL | Responsabilidade |
|-----|-----------------|-----------------|
| `accounts` | `/access/` | Usuários, perfis, grupos, permissões |
| `dempam` | `/dempam/` | UAs, prédios, setores, localizações |
| `demands` | `/demands/` | Demandas e tickets internos |
| `dimms` | `/dimms/` | Bens de consumo, estoque, contratos, licitações |
| `dimrcbp` | `/dimrcbp/` | Bens permanentes, movimentações, inventário |

Cada app segue a mesma estrutura interna:

```
app/
├── models/         # ou models.py — entidades do domínio
├── views/          # views divididas por arquivo de contexto
├── templates/      # HTML do app
├── migrations/     # migrações geradas automaticamente
├── urls.py
├── admin.py
└── tests.py (ou tests/)
```

---

## Convenções do projeto

### Views

- Todas as views usam `@login_required` — não deixar view sem proteção.
- Views administrativas (gestão de usuários, grupos) usam `@management_required` de `accounts.decorators`.
- Views retornam `render()` ou `redirect()` — sem DRF, sem API REST. O sistema é server-rendered.
- Autocomplete/busca dinâmica retorna `JsonResponse` diretamente na view.

### Models

- Códigos de documentos são gerados automaticamente no `save()` com padrão `PREFIXO-YYYY-XXXX` (ex.: `SBC-2026-0001`, `DEM-2026-0042`).
- `HistoricoMudanca` e `MovimentacaoBem` em `dimrcbp` são audit trail — nunca deletar registros dessas tabelas.
- `sincronizar_atribuicao()` em `dimrcbp/models.py` é chamada via signal (`signals.py`) quando o gestor de uma UA muda — ressincroniza `AtribuicaoBem` de todos os bens da UA.
- Ao mover um bem permanente, sempre atualizar `HistoryUas` (UA atual) além de criar `MovimentacaoBem`.

### Templates

- Template base global: `templates/global/base.html` — todos os templates estendem este.
- Template tag customizada: `accounts/templatetags/access_tags.py` — filtro `|get_item:key` para acessar dicionários por chave variável nos templates.
- Templates ficam dentro do próprio app (`app/templates/app/`), exceto os globais que ficam em `templates/global/`.

### Autenticação

- Em desenvolvimento: form padrão do Django em `/login/`.
- Em produção/staging: OIDC via Authentik em `/oidc/authenticate/` com PKCE e RS256.
- `OIDC_CREATE_USER = False` — usuários precisam ser criados manualmente antes do primeiro login SSO.
- Após login, redireciona para `/home/`.

### Settings por ambiente

| Arquivo | Banco | Auth | Uso |
|---------|-------|------|-----|
| `development.py` | SQLite | Form Django | Desenvolvimento local |
| `local.py` | PostgreSQL (Docker) | Form Django | Docker local |
| `staging.py` | PostgreSQL | OIDC | Homologação |
| `production.py` | PostgreSQL | OIDC | Produção MPPE |

---

## Fluxos de negócio críticos

### Solicitação de bem de consumo (DIMMS)

`SolicitacaoCatalogoConsumo` → aprovação pelo gestor → baixa automática no `Estoque` → status `ENTREGUE`.

Nunca baixar estoque manualmente — a baixa acontece na aprovação da solicitação.

### Tramitação de solicitação direta (DIMMS)

`Solicitacao` segue o fluxo: `Em Atendimento → Aguardando Separação → Separada → Em Expedição → Recebida`. A flag `stock_deducted` indica se o estoque já foi baixado — checar antes de qualquer operação de estoque.

### Transferência de bem permanente (DIMRCBP)

`SolicitacaoTransferencia` → aprovação → `MovimentacaoBem` criado → `HistoryUas` atualizado → `HistoricoMudanca` registrado → PDF do termo gerado via ReportLab.

---

## Arquitetura detalhada

Veja [`docs/architecture.md`](docs/architecture.md) para os diagramas C4 completos (contexto, containers, componentes, entidades e fluxos de sequência).

---

## Git

Branch naming:
```
feat/descricao-curta
fix/descricao-curta
refactor/descricao-curta
docs/descricao-curta
chore/descricao-curta
```

Commits seguem [Conventional Commits](https://www.conventionalcommits.org/pt-br). Veja [`CONTRIBUTING.md`](CONTRIBUTING.md) para o guia completo.
