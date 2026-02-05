from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User

# --- Modelo de Setor ---
class Setor(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nome

# --- Modelo de Bloco ---
class Bloco(models.Model):
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE, related_name='blocos', null=True, blank=True)
    nome = models.CharField(max_length=100, unique=True, help_text="Ex: Bloco A, Prateleira 12-C")
    def __str__(self):
        return self.nome

# --- Modelo Principal de Item ---
class Item(models.Model):
    CATEGORIA_CHOICES = [
        ('PERMANENTE', 'Bens Permanentes'),
        ('CONSUMO', 'Bens de Consumo'),
        ('TI', 'Bens de TI'),
    ]
    
    TIPO_CONSUMO_CHOICES = [
        ('ALIMENTOS', 'Alimentos'),
        ('COPA-COZINHA', 'Copa-Cozinha'),
        ('EXPEDIENTE', 'Expediente'),
        ('PAPEIS PARA EXPEDIENTE', 'Papéis para Expediente'),
        ('ESTOCAGEM', 'Estocagem'),
        ('CONFECCAO', 'Confecção'),
        ('TONERS', 'Toners'),
        ('INFORMATICA', 'Informática'),
        ('LIMPEZA', 'Limpeza'),
        ('PAPEIS PARA LIMPEZA', 'Papéis para Limpeza'),
        ('DOMISSANITARIOS', 'Domissanitários'),
        ('EPI', 'EPI'),
        ('MANUTENCAO', 'Manutenção'),
        ('OUTROS', 'Outros'),
    ]

    # --- Identificação (OBRIGATÓRIOS) ---
    numero_identificacao = models.IntegerField(unique=True, primary_key=True, verbose_name="Tombo / Nº de Identificação")
    nome = models.CharField(max_length=200, verbose_name="Nome do Item")
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='PERMANENTE', verbose_name="Categoria do Bem")

    # --- Detalhes e Descrição (Estavam faltando e geravam o erro) ---
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição") 
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Valor Unitário")
    numero_de_serie = models.CharField(max_length=100, blank=True, null=True, verbose_name="Número de Série")
    
    # --- Outros Campos ---
    foto_do_bem = models.ImageField(upload_to='fotos_itens/', blank=True, null=True, verbose_name="Foto do Bem")
    localizacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Localização")
    marca = models.CharField(max_length=100, blank=True, null=True, verbose_name="Marca")
    modelo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Modelo")
    estado_de_conservacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Estado de Conservação")
    
    # --- Campos Específicos ---
    tipo_consumo = models.CharField(max_length=50, choices=TIPO_CONSUMO_CHOICES, blank=True, null=True, verbose_name="Tipo de Bem de Consumo")
    
    # Estoque
    qtd_estoque = models.IntegerField(default=0, blank=True, null=True, verbose_name="Quantidade em Estoque")
    qtde = models.IntegerField(default=1, verbose_name="Quantidade Total") 

    validade = models.DateField(blank=True, null=True, verbose_name="Data de Validade")
    codigo_efisco = models.CharField(max_length=100, blank=True, null=True, verbose_name="Código do E-FISCO")
    
    # --- Relacionamentos ---
    bloco = models.ForeignKey(Bloco, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Bloco de Armazenamento")
    lote = models.CharField(max_length=100, blank=True, null=True, verbose_name="Identificador do Lote")
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.numero_identificacao})"

# --- Modelo de Movimentação ---
class Movimentacao(models.Model):
    TIPO_CHOICES = [('ENTRADA', 'Entrada'), ('SAIDA', 'Saída')]
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    quantidade = models.PositiveIntegerField()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    data_hora = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True, null=True)
    documento_pdf = models.FileField(upload_to='movimentacoes_pdf/', blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.item.nome}"

# --- Modelos de Requisição ---
class Requisicao(models.Model):
    STATUS_CHOICES = [('PENDENTE', 'Pendente'), ('APROVADO', 'Aprovado'), ('REJEITADO', 'Rejeitado')]
    TIPO_REQUISICAO_CHOICES = [('SAIDA', 'Saída'), ('ENTRADA', 'Entrada')]
    
    tipo = models.CharField(max_length=10, choices=TIPO_REQUISICAO_CHOICES, default='SAIDA')
    requisitante = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_requisicao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDENTE')
    observacao_geral = models.TextField(blank=True, null=True)
    documento = models.FileField(upload_to='requisicoes_docs/', blank=True, null=True)

class ItemRequisitado(models.Model):
    requisicao = models.ForeignKey(Requisicao, on_delete=models.CASCADE, related_name='itens_pedidos')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()