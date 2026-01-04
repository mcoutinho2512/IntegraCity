from django.contrib import admin
from .models import Evento, DataEvento, SecLocaisEvento

# ==================== GESTÃO DE EVENTOS ====================

class DataEventoInline(admin.TabularInline):
    model = DataEvento
    extra = 1
    fields = ['data_conce', 'data_inicio', 'data_fim']


class SecLocaisEventoInline(admin.TabularInline):
    model = SecLocaisEvento
    extra = 0
    fields = ['bairro', 'end', 'location']


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ['nome_evento', 'tipo', 'status', 'criti', 'respeven', 'principal']
    list_filter = ['status', 'tipo', 'criti', 'respeven', 'principal']
    search_fields = ['nome_evento', 'descri']
    inlines = [DataEventoInline, SecLocaisEventoInline]
    readonly_fields = ['criti', 'med']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome_evento', 'descri', 'tipo', 'status', 'principal')
        }),
        ('Localização', {
            'fields': ('endere', 'endereco', 'tipo_forma', 'raio', 'tem_poligono', 'poligono_coords')
        }),
        ('Operacional', {
            'fields': ('estr', 'cpe', 'qt', 'forma', 'respeven', 'alinha')
        }),
        ('Criticidade', {
            'fields': (
                ('criti', 'med'),
                'local_criti', 'data_criti', 'hora_criti',
                'mobi_criti', 'pub_criti', 'exp_criti',
                'fp_criti', 'efe_criti', 'pop_criti', 'pt_criti'
            ),
            'classes': ['collapse']
        }),
        ('Observações', {
            'fields': ('pontos_atencao', 'fonte', 'arquivo')
        }),
    )


@admin.register(DataEvento)
class DataEventoAdmin(admin.ModelAdmin):
    list_display = ['evento', 'data_inicio', 'data_fim']
    list_filter = ['data_inicio']
    search_fields = ['evento__nome_evento']
