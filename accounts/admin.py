from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html, mark_safe

from accounts.models import Profile


# ─── Profile inline dentro do User ───────────────────────────────────────────

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name = 'Perfil'
    verbose_name_plural = 'Perfil'
    fields = ('photo', 'phone', 'photo_preview')
    readonly_fields = ('photo_preview',)

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:50%;">',
                obj.photo.url
            )
        return '—'
    photo_preview.short_description = 'Foto atual'


# ─── User com Profile embutido ────────────────────────────────────────────────

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

    list_display  = ('username', 'get_full_name', 'email', 'photo_thumb', 'group_list', 'is_active', 'is_staff')
    list_filter   = ('is_active', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering      = ('username',)

    def photo_thumb(self, obj):
        try:
            if obj.profile.photo:
                return format_html(
                    '<img src="{}" style="width:32px;height:32px;object-fit:cover;border-radius:50%;">',
                    obj.profile.photo.url
                )
        except Profile.DoesNotExist:
            pass
        return '—'
    photo_thumb.short_description = 'Foto'

    def group_list(self, obj):
        groups = obj.groups.all()
        if not groups:
            return '—'
        chips = ''.join(
            format_html(
                '<span style="display:inline-block;padding:2px 8px;margin:1px;border-radius:999px;'
                'background:#f5f3ff;border:1px solid #ddd6fe;color:#6d28d9;font-size:11px;font-weight:600;">'
                '{}</span>',
                g.name
            )
            for g in groups
        )
        return mark_safe(chips)
    group_list.short_description = 'Grupos'


# ─── Profile standalone ───────────────────────────────────────────────────────

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'phone', 'photo_thumb', 'has_photo')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
    readonly_fields = ('photo_preview',)

    fieldsets = (
        (None, {
            'fields': ('user', 'phone')
        }),
        ('Foto', {
            'fields': ('photo', 'photo_preview')
        }),
    )

    def photo_thumb(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="width:32px;height:32px;object-fit:cover;border-radius:50%;">',
                obj.photo.url
            )
        return '—'
    photo_thumb.short_description = 'Foto'

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="width:80px;height:80px;object-fit:cover;border-radius:50%;">',
                obj.photo.url
            )
        return '—'
    photo_preview.short_description = 'Pré-visualização'

    def has_photo(self, obj):
        return bool(obj.photo)
    has_photo.boolean = True
    has_photo.short_description = 'Tem foto'


# ─── Re-registra o User com o admin customizado ──────────────────────────────

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
