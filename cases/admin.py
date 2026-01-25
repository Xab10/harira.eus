from django.contrib import admin
from .models import Case, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("kind", "name")
    list_filter = ("kind",)
    search_fields = ("name",)


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("cic", "centro_medico", "fecha", "publicado", "created_by")
    list_filter = ("publicado", "fecha", "centro_medico")
    search_fields = ("cic", "centro_medico", "diagnostico_inicial", "comentarios", "publicado_en")

