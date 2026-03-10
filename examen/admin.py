from django.contrib import admin
from .models import Oposicion, Bloque, Tema, Capitulo, Articulo, Pregunta, Examen, RespuestaUsuario


# ── Inlines ──────────────────────────────────────────────────────────────────

class BloqueInline(admin.TabularInline):
    model = Bloque
    extra = 1
    fields = ('orden', 'titulo')


class TemaInline(admin.TabularInline):
    model = Tema
    extra = 1
    fields = ('orden', 'titulo')


class CapituloInline(admin.TabularInline):
    model = Capitulo
    extra = 1
    fields = ('orden', 'titulo', 'documentacion')


class ArticuloInline(admin.StackedInline):
    model = Articulo
    extra = 0
    fields = ('numero', 'titulo', 'contenido')
    show_change_link = True


class PreguntaInline(admin.TabularInline):
    model = Pregunta
    extra = 0
    fields = ('enunciado', 'respuesta_correcta')
    show_change_link = True


class RespuestaUsuarioInline(admin.TabularInline):
    model = RespuestaUsuario
    extra = 0
    readonly_fields = ('pregunta', 'respuesta_seleccionada', 'es_correcta')
    can_delete = False


# ── ModelAdmins ───────────────────────────────────────────────────────────────

@admin.register(Oposicion)
class OposicionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'num_preguntas', 'penalizacion', 'descripcion')
    search_fields = ('nombre',)
    inlines = [BloqueInline]


@admin.register(Bloque)
class BloqueAdmin(admin.ModelAdmin):
    list_display = ('orden', 'titulo', 'oposicion')
    list_filter = ('oposicion',)
    ordering = ('orden',)
    inlines = [TemaInline]


@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'bloque', 'orden')
    list_filter = ('bloque',)
    search_fields = ('titulo',)
    inlines = [CapituloInline]


@admin.register(Capitulo)
class CapituloAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tema', 'orden')
    list_filter = ('tema__bloque',)
    search_fields = ('titulo',)
    inlines = [ArticuloInline]


@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    list_display = ('numero', 'titulo', 'capitulo')
    list_filter = ('capitulo__tema__bloque',)
    search_fields = ('titulo', 'numero', 'contenido')
    inlines = [PreguntaInline]


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('enunciado_corto', 'respuesta_correcta', 'articulo')
    list_filter = (
        'respuesta_correcta',
        'articulo__capitulo__tema__bloque',
    )
    search_fields = ('enunciado', 'respuesta_a', 'respuesta_b', 'respuesta_c', 'respuesta_d')

    @admin.display(description='Enunciado')
    def enunciado_corto(self, obj):
        return obj.enunciado[:80] + '...' if len(obj.enunciado) > 80 else obj.enunciado


@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'tipo', 'oposicion', 'puntuacion', 'fecha_finalizacion')
    list_filter = ('tipo', 'oposicion', 'usuario')
    readonly_fields = ('fecha_creacion', 'fecha_finalizacion', 'puntuacion',
                       'respuestas_correctas', 'respuestas_erroneas')
    inlines = [RespuestaUsuarioInline]


@admin.register(RespuestaUsuario)
class RespuestaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('examen', 'pregunta', 'respuesta_seleccionada', 'es_correcta')
    list_filter = ('es_correcta',)
    readonly_fields = ('es_correcta',)


# ── Cabecera del panel ────────────────────────────────────────────────────────
admin.site.site_header = 'Panel de Administración — OPOSICIONES'
admin.site.index_title = 'Gestión de contenido y usuarios'
admin.site.site_title = 'Admin Oposiciones'
