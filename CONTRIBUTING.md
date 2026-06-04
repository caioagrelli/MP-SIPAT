# Como Colaborar

Obrigado pelo interesse em contribuir com o SIPAT! Este guia descreve o processo para reportar problemas, sugerir melhorias e enviar código.

---

## Índice

- [Pré-requisitos](#pré-requisitos)
- [Configurando o ambiente](#configurando-o-ambiente)
- [Fluxo de trabalho com Git](#fluxo-de-trabalho-com-git)
- [Convenções de commits](#convenções-de-commits)
- [Abrindo um Pull Request](#abrindo-um-pull-request)
- [Reportando bugs](#reportando-bugs)
- [Sugerindo melhorias](#sugerindo-melhorias)

---

## Pré-requisitos

- Python 3.12+
- Git

---

## Configurando o ambiente

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd sipat
```

### 2. Crie e ative um ambiente virtual

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto. Consulte `.env.example` (se disponível) ou o time de desenvolvimento para obter os valores necessários.

### 5. Aplique as migrações e inicie o servidor

```bash
python manage.py migrate
python manage.py runserver
```

O servidor estará disponível em `http://localhost:8000`.

> **Ambiente local com Docker (PostgreSQL)**
> Se preferir usar PostgreSQL localmente em vez do SQLite, utilize o Docker Compose:
> ```bash
> docker compose up
> ```
> Certifique-se de que o `.env` possui as variáveis `DB_NAME`, `DB_USER` e `DB_PASSWORD` configuradas.

---

## Fluxo de trabalho com Git

O repositório segue um modelo de duas branches principais:

| Branch | Propósito | Atualizada por |
|--------|-----------|---------------|
| `development` | Integração contínua — recebe todas as features e fixes | PRs de branches de trabalho |
| `main` | Código estável em produção | PR de `development` → `main` (release) |

**Nunca abra PR diretamente para `main`.** A `main` só é atualizada via PR de `development`.

### Passo a passo

1. Crie uma branch a partir de `development`:

```bash
git checkout development
git pull origin development
git checkout -b tipo/descricao-curta
```

Exemplos de nomes de branch:
- `feat/filtro-por-contrato`
- `fix/calculo-saldo-ativo`
- `refactor/views-solicitacoes`

2. Faça suas alterações em commits pequenos e coesos.

3. Antes de abrir o PR, sincronize com `development`:

```bash
git fetch origin
git rebase origin/development
```

4. Abra o PR com destino em **`development`**.

### Release para produção

Quando `development` estiver estável e validado em staging, um mantenedor abre um PR de `development` → `main`. Esse PR representa uma release e deve conter no título o escopo das mudanças (ex.: `release: v1.2.0 — filtros de estoque e inventário`).

---

## Convenções de commits

Use o padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br):

```
<tipo>(<escopo>): <descrição curta no imperativo>
```

| Tipo | Quando usar |
|------|-------------|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `refactor` | Refatoração sem mudança de comportamento |
| `docs` | Documentação |
| `style` | Formatação, sem alteração de lógica |
| `test` | Adição ou correção de testes |
| `chore` | Tarefas de manutenção (deps, CI, etc.) |
| `data` | Dados de migração ou seed |

**Exemplos:**
```
feat(solicitacoes): adiciona filtro por período na listagem
fix(estoque): corrige baixa duplicada ao expedir lote
docs: atualiza README com instruções de deploy
```

---

## Abrindo um Pull Request

1. O PR deve ter como destino a branch **`developmentment`**, nunca `main`.
2. Certifique-se de que o código está funcionando e sem erros de lint.
3. Descreva claramente **o que** foi feito e **por quê** no corpo do PR.
4. Referencie a issue relacionada, se houver (ex.: `Closes #42`).
5. Aguarde revisão de pelo menos um mantenedor antes do merge.

---

## Reportando bugs

Abra uma issue descrevendo:

- **O que aconteceu** — comportamento observado
- **O que era esperado** — comportamento correto
- **Como reproduzir** — passos detalhados
- **Ambiente** — versão do Python, sistema operacional, navegador (se aplicável)

---

## Sugerindo melhorias

Abra uma issue com o prefixo `[Sugestão]` no título e descreva:

- O problema ou limitação atual
- A solução proposta
- Qualquer alternativa considerada

---

Dúvidas? Entre em contato com a equipe de desenvolvimento do DEMPAM/MPPE.
