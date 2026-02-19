from django.db import models
    
class AcaoPermanente(models.TextChoices):
    solicitacao = 'SOLICITACAO', 'Solicitação'
    devolucao = 'DEVOLUCAO', 'Devolução'
    tranferencia = 'TRANSFERENCIA', 'Transferência'
    
class TipoLocalizacao(models.TextChoices):
    pallet = 'PALLET', 'Pallet'
    prateleira = 'PRATELEIRA', 'Prateleira'
    
class UnidadesMedida(models.TextChoices):
    metro = 'METRO', 'Metro'
    unidade = 'UNIDADE', 'Unidade' 
    quilograma = 'QUILOGRAMA', 'Quilograma'
    litro = 'LITRO', 'Litro'
    pacote = 'PACOTE', 'Pacote'
    caixa = 'CAIXA', 'Caixa'
    
    
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
    
class GrupoConsumo(models.TextChoices):
    alimento = 'ALIMENTO', 'Alimento'
    confeccao = 'CONFECCAO', 'Confecção'
    copa_cozinha = 'COPA_COZINHA', 'Copa / Cozinha'
    domissanitario = 'DOMISSANITARIO', 'Domissanitário'
    eletrica = 'ELETRICA', 'Elétrica'
    epi = 'EPI', 'EPI'
    hidrosanitario = 'HIDROSANITARIO', 'Hidrossanitário'
    informatica = 'INFORMATICA', 'Informática'
    limpeza = 'LIMPEZA', 'Limpeza'
    manutencao = 'MANUTENCAO', 'Manutenção'
    marcenaria = 'MARCENARIA', 'Marcenaria'
    pintura = 'PINTURA', 'Pintura'
    papeis_expediente = 'PAPEIS_EXPEDIENTE', 'Papéis de Expediente'
    papeis_limpeza = 'PAPEIS_LIMPEZA', 'Papéis de Limpeza'
    refrigeracao = 'REFRIGERACAO', 'Refrigeração'
    toner = 'TONER', 'Toner'
    
class Cota(models.TextChoices):
    principal = 'PRINCIPAL', 'Principal'
    reservada = 'RESERVADA', 'Reservada'