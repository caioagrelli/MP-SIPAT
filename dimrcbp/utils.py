import os
from django.db import models, transaction, IntegrityError
from django.utils import timezone

# --- Paths ---

def caminho_benspermanentes(instance, filename):
    tombamento = instance.tombo or 'sem_tombo'
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{tombamento}{ext}'

    return f'bens/permanentes/{nome_aquivo}'

def caminho_catalogo(instance, filename):
    efisco = instance.efisco or 'sem_efisco'
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{efisco}{ext}'

    return f'bens/permanentes/catalogo/{nome_aquivo}'

def caminho_inventario(instance, filename):
    periodo = getattr(instance, 'n_inventario', None)
    year = periodo.inicio.year if periodo and periodo.inicio else 'sem_data'
    tombo = instance.bem.tombo if getattr(instance, 'bem', None) else 'sem_tombo'
    ext = os.path.splitext(filename)[1]
    return f'bens/permanentes/inventarios/{year}/{tombo}{ext}'


# Gera o próximo código sequencial do ano (ex.: STF-2026-0001) pra um campo único de um model.
# Baseado no MAIOR número já usado no ano — não em count() — pra não colidir quando algum
# código no meio da sequência foi apagado (deixando "buracos" que fariam count()+1 repetir
# um número que já existe).
def gerar_proximo_codigo(model, campo, prefixo, digitos=4):
    ano = timezone.now().year
    prefixo_ano = f'{prefixo}-{ano}-'
    ultimo_codigo = (
        model.objects
        .filter(**{f'{campo}__startswith': prefixo_ano})
        .order_by(f'-{campo}')
        .values_list(campo, flat=True)
        .first()
    )
    ultimo_numero = int(ultimo_codigo.rsplit('-', 1)[-1]) if ultimo_codigo else 0
    return f'{prefixo_ano}{ultimo_numero + 1:0{digitos}d}'


# Gera o código (via gerar_proximo_codigo) e chama save_callable dentro de uma transação,
# tentando de novo com o próximo número se colidir por causa de uma corrida entre requisições
# simultâneas. Só engole o IntegrityError se ele for mesmo sobre esse campo — qualquer outro
# erro (ex.: FK obrigatória faltando) sobe na hora, sem mascarar a causa real.
def salvar_com_codigo_sequencial(instance, campo, prefixo, save_callable, *args, digitos=4, tentativas=5, **kwargs):
    model = type(instance)
    for _ in range(tentativas):
        setattr(instance, campo, gerar_proximo_codigo(model, campo, prefixo, digitos))
        try:
            with transaction.atomic():
                save_callable(*args, **kwargs)
            return
        except IntegrityError as e:
            if campo not in str(e):
                raise
            setattr(instance, campo, '')
    raise IntegrityError(f'Não foi possível gerar um código único ({prefixo}) após {tentativas} tentativas.')


# --- Choices ---
class AcaoPermanente(models.TextChoices):
    solicitacao = 'SOLICITACAO', 'Solicitação'
    devolucao = 'DEVOLUCAO', 'Devolução'
    tranferencia = 'TRANSFERENCIA', 'Transferência'

class SituacaoFisica(models.TextChoices):
    antieconomico = 'ANTIECONOMICO', 'Antieconômico'
    em_uso = 'EM_USO', 'Em Uso'
    irrecuperavel = 'IRRECUPERAVEL', 'Irrecuperável'
    ocioso = 'OCIOSO', 'Ocioso'
    recuperavel = 'RECUPERAVEL', 'Recuperável'
    
class EstadoConservacao(models.TextChoices):
    bom = 'BOM', 'Bom'
    novo = 'NOVO', 'Novo'
    precario = 'PRECARIO', 'Precário'
    regular = 'REGULAR', 'Regular'
    sucata = 'SUCATA', 'Sucata'

class SituacaoInventario(models.TextChoices):
    bom = 'BOM', 'Bom'
    regular = 'REGULAR', 'Regular'
    precario = 'PRECARIO', 'Precário'
    sucata = 'SUCATA', 'Sucata'

class GruposPermanentes(models.TextChoices):
    condicionador = 'CONDICIONADOR', 'Condicionador de Ar'
    eletroeletronico = 'ELETROELETRONICO', 'Eletroeletrônico'
    tic = 'TIC', 'Equipammentos de TIC'
    mobiliario = 'MOBILIARIO', 'Mobiliário'
    outros = 'OUTROS', 'Outros'
    
class StatusSolicitacaoCatalogo(models.TextChoices):
    pendente  = 'PENDENTE',  'Pendente'
    aprovada  = 'APROVADA',  'Aprovada'
    rejeitada = 'REJEITADA', 'Rejeitada'
    cancelada = 'CANCELADA', 'Cancelada'

class StatusSolicitacaoTransferencia(models.TextChoices):
    pendente  = 'PENDENTE',  'Pendente'
    aprovada  = 'APROVADA',  'Aprovada'
    rejeitada = 'REJEITADA', 'Rejeitada'
    cancelada = 'CANCELADA', 'Cancelada'

class Cores(models.TextChoices):
    BRANCO = 'BRANCO', 'Branco'
    PRETO = 'PRETO', 'Preto'
    CINZA = 'CINZA', 'Cinza'
    VERMELHO = 'VERMELHO', 'Vermelho'
    AZUL = 'AZUL', 'Azul'
    VERDE = 'VERDE', 'Verde'
    AMARELO = 'AMARELO', 'Amarelo'
    LARANJA = 'LARANJA', 'Laranja'
    ROXO = 'ROXO', 'Roxo'
    ROSA = 'ROSA', 'Rosa'
    MARROM = 'MARROM', 'Marrom'
    AZUL_CLARO = 'AZUL_CLARO', 'Azul claro'
    AZUL_ESCURO = 'AZUL_ESCURO', 'Azul escuro'
    VERDE_CLARO = 'VERDE_CLARO', 'Verde claro'
    VERDE_ESCURO = 'VERDE_ESCURO', 'Verde escuro'
    VERMELHO_ESCURO = 'VERMELHO_ESCURO', 'Vermelho escuro'
    AMARELO_CLARO = 'AMARELO_CLARO', 'Amarelo claro'
    CINZA_CLARO = 'CINZA_CLARO', 'Cinza claro'
    CINZA_ESCURO = 'CINZA_ESCURO', 'Cinza escuro'
    BEGE = 'BEGE', 'Bege'
    CREME = 'CREME', 'Creme'
    VINHO = 'VINHO', 'Vinho'
    BORDO = 'BORDO', 'Bordô'
    TURQUESA = 'TURQUESA', 'Turquesa'
    LILAS = 'LILAS', 'Lilás'
    SALMAO = 'SALMAO', 'Salmão'
    DOURADO = 'DOURADO', 'Dourado'
    PRATEADO = 'PRATEADO', 'Prateado'
    BRANCO_GELO = 'BRANCO_GELO', 'Branco gelo'
    BRANCO_FOSCO = 'BRANCO_FOSCO', 'Branco fosco'
    BRANCO_BRILHANTE = 'BRANCO_BRILHANTE', 'Branco brilhante'
    PRETO_FOSCO = 'PRETO_FOSCO', 'Preto fosco'
    PRETO_BRILHANTE = 'PRETO_BRILHANTE', 'Preto brilhante'
    GRAFITE = 'GRAFITE', 'Grafite'
    INOX = 'INOX', 'Inox'
    CROMADO = 'CROMADO', 'Cromado'
    AMADEIRADO = 'AMADEIRADO', 'Amadeirado'
    CARVALHO = 'CARVALHO', 'Carvalho'
    IMBUIA = 'IMBUIA', 'Imbuia'
    MOGNO = 'MOGNO', 'Mogno'
    NOGUEIRA = 'NOGUEIRA', 'Nogueira'
    
