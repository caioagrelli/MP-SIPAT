from django.contrib import admin
from .models import DemandType, Demand, DemandAssignment, DemandAttachment, DemandUpdate


@admin.register(DemandType)
class DemandTypeAdmin(admin.ModelAdmin):
    list_display  = ('name', 'color', 'icon', 'is_active', 'created_at')
    list_filter   = ('is_active',)
    search_fields = ('name',)
    filter_horizontal = ('allowed_groups',)


class DemandAssignmentInline(admin.TabularInline):
    model  = DemandAssignment
    extra  = 1
    fields = ('user', 'can_change_status')


class DemandAttachmentInline(admin.TabularInline):
    model          = DemandAttachment
    extra          = 0
    readonly_fields = ('uploaded_by', 'uploaded_at', 'name')


class DemandUpdateInline(admin.StackedInline):
    model           = DemandUpdate
    extra           = 0
    readonly_fields = ('author', 'created_at')
    fields          = ('author', 'comment', 'status_change', 'file', 'created_at')


@admin.register(Demand)
class DemandAdmin(admin.ModelAdmin):
    list_display  = ('code', 'title', 'demand_type', 'priority', 'status', 'ua', 'created_by', 'deadline', 'created_at')
    list_filter   = ('status', 'priority', 'demand_type')
    search_fields = ('code', 'title', 'description')
    readonly_fields = ('code', 'created_at', 'updated_at')
    date_hierarchy  = 'created_at'
    inlines         = [DemandAssignmentInline, DemandAttachmentInline, DemandUpdateInline]
    fieldsets = (
        (None, {
            'fields': ('code', 'demand_type', 'title', 'description'),
        }),
        ('Classificação', {
            'fields': ('priority', 'status', 'deadline', 'ua'),
        }),
        ('Responsável', {
            'fields': ('created_by',),
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(DemandAssignment)
class DemandAssignmentAdmin(admin.ModelAdmin):
    list_display  = ('demand', 'user', 'can_change_status')
    list_filter   = ('can_change_status',)
    search_fields = ('demand__code', 'demand__title', 'user__username')


@admin.register(DemandAttachment)
class DemandAttachmentAdmin(admin.ModelAdmin):
    list_display    = ('name', 'demand', 'uploaded_by', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
    search_fields   = ('name', 'demand__code')


@admin.register(DemandUpdate)
class DemandUpdateAdmin(admin.ModelAdmin):
    list_display    = ('demand', 'author', 'status_change', 'created_at')
    list_filter     = ('status_change',)
    readonly_fields = ('created_at',)
    search_fields   = ('demand__code', 'author__username', 'comment')
