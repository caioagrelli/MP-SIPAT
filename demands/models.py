from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone


# ─── Choices ──────────────────────────────────────────────────────────────────

class Priority(models.TextChoices):
    low    = 'low',    'Baixa'
    medium = 'medium', 'Média'
    high   = 'high',   'Alta'
    urgent = 'urgent', 'Urgente'


class Status(models.TextChoices):
    open        = 'open',        'Aberta'
    in_progress = 'in_progress', 'Em Andamento'
    done        = 'done',        'Concluída'


# ─── Paths de upload ──────────────────────────────────────────────────────────

def demand_attachment_path(instance, filename):
    return f'demands/{instance.demand.code}/attachments/{filename}'


def update_attachment_path(instance, filename):
    return f'demands/{instance.update.demand.code}/updates/{filename}'


# ─── Tipo de Demanda ──────────────────────────────────────────────────────────

class DemandType(models.Model):
    name        = models.CharField(max_length=80, unique=True, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    color       = models.CharField(max_length=7, default='#1d4ed8', verbose_name='Cor')
    icon        = models.CharField(max_length=10, default='📋', verbose_name='Ícone')
    is_active   = models.BooleanField(default=True, verbose_name='Ativo')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    # Grupos que podem CRIAR demandas desse tipo
    allowed_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name='demand_types',
        verbose_name='Grupos com permissão para criar',
    )

    class Meta:
        verbose_name        = 'Tipo de Demanda'
        verbose_name_plural = 'Tipos de Demanda'
        ordering            = ['name']

    def __str__(self):
        return self.name


# ─── Demanda ──────────────────────────────────────────────────────────────────

class Demand(models.Model):
    code        = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Código')
    demand_type = models.ForeignKey(DemandType, on_delete=models.PROTECT, verbose_name='Tipo')
    title       = models.CharField(max_length=120, verbose_name='Título')
    description = models.TextField(verbose_name='Descrição')
    priority    = models.CharField(max_length=10, choices=Priority.choices, default=Priority.medium, verbose_name='Prioridade')
    status      = models.CharField(max_length=15, choices=Status.choices, default=Status.open, verbose_name='Status')
    deadline    = models.DateField(blank=True, null=True, verbose_name='Prazo')

    created_by  = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='demands_created',
        verbose_name='Criado por',
    )

    assigned_to = models.ManyToManyField(
        User,
        blank=True,
        related_name='demands_assigned',
        verbose_name='Atribuído a',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    # ── Escalabilidade futura ──────────────────────────────────────────────────
    # Para vincular a um objeto do site (ex: Solicitacao, Artefato), usar:
    #   from django.contrib.contenttypes.fields import GenericForeignKey
    #   from django.contrib.contenttypes.models import ContentType
    #   content_type   = ForeignKey(ContentType, null=True, blank=True)
    #   object_id      = PositiveIntegerField(null=True, blank=True)
    #   linked_object  = GenericForeignKey('content_type', 'object_id')
    # ──────────────────────────────────────────────────────────────────────────

    class Meta:
        verbose_name        = 'Demanda'
        verbose_name_plural = 'Demandas'
        ordering            = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.code:
            ano    = timezone.now().year
            ultimo = Demand.objects.filter(code__startswith=f'DEM-{ano}').count() + 1
            self.code = f'DEM-{ano}-{ultimo:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.title}'

    @property
    def is_overdue(self):
        if self.deadline and self.status != Status.done:
            return self.deadline < timezone.now().date()
        return False


# ─── Anexos da Demanda ────────────────────────────────────────────────────────

class DemandAttachment(models.Model):
    demand      = models.ForeignKey(Demand, on_delete=models.CASCADE, related_name='attachments', verbose_name='Demanda')
    file        = models.FileField(upload_to=demand_attachment_path, verbose_name='Arquivo')
    name        = models.CharField(max_length=120, blank=True, verbose_name='Nome do arquivo')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Enviado por')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Enviado em')

    class Meta:
        verbose_name        = 'Anexo'
        verbose_name_plural = 'Anexos'

    def save(self, *args, **kwargs):
        # Usa o nome original do arquivo se não informado
        if not self.name and self.file:
            self.name = self.file.name.split('/')[-1]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or str(self.file)

    @property
    def is_image(self):
        return self.file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))


# ─── Atualizações / Histórico ─────────────────────────────────────────────────

class DemandUpdate(models.Model):
    demand        = models.ForeignKey(Demand, on_delete=models.CASCADE, related_name='updates', verbose_name='Demanda')
    author        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Autor')
    comment       = models.TextField(verbose_name='Comentário')
    status_change = models.CharField(max_length=15, blank=True, choices=Status.choices, verbose_name='Mudança de status')
    file          = models.FileField(upload_to=update_attachment_path, blank=True, null=True, verbose_name='Arquivo anexado')
    created_at    = models.DateTimeField(auto_now_add=True, verbose_name='Postado em')

    class Meta:
        verbose_name        = 'Atualização'
        verbose_name_plural = 'Atualizações'
        ordering            = ['created_at']

    def __str__(self):
        return f'Update de {self.demand.code} por {self.author}'
