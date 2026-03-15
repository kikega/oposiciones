from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Oposicion, Tema, Capitulo, Articulo, Pregunta,
    Examen, RespuestaUsuario, NotaEstudio, PerfilUsuario,
    RecursoTema, ProgresoEstudio
)


# ── Inlines ───────────────────────────────────────────────────────────────────

class TemaInline(admin.TabularInline):
    model = Tema.oposiciones.through
    extra = 1
    verbose_name = "Tema vinculado"
    verbose_name_plural = "Temas vinculados"


class CapituloInline(admin.TabularInline):
    model = Capitulo
    extra = 1
    fields = ('orden', 'titulo', 'importancia', 'es_modificacion_reciente')
    show_change_link = True


class ArticuloInline(admin.StackedInline):
    model = Articulo
    extra = 0
    fields = ('numero', 'contenido')
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


class RecursoTemaInline(admin.TabularInline):
    model = RecursoTema
    extra = 1


# ── ModelAdmins ───────────────────────────────────────────────────────────────

@admin.register(Oposicion)
class OposicionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'num_preguntas', 'penalizacion', 'descripcion')
    search_fields = ('nombre',)
    inlines = [TemaInline]


@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'bloque', 'orden', 'get_oposiciones')
    list_filter = ('oposiciones',)
    search_fields = ('titulo', 'bloque')  # requerido para autocomplete
    inlines = [CapituloInline]

    @admin.display(description='Oposiciones')
    def get_oposiciones(self, obj):
        return ", ".join(o.nombre for o in obj.oposiciones.all())


@admin.register(Capitulo)
class CapituloAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'orden', 'tema', 'importancia', 'es_modificacion_reciente')
    list_filter = ('tema__oposiciones', 'importancia', 'es_modificacion_reciente')
    search_fields = ('titulo', 'tema__titulo')  # requerido para autocomplete
    inlines = [ArticuloInline, RecursoTemaInline]
    autocomplete_fields = ['tema']


@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    list_display = ('numero', 'get_capitulo', 'get_tema', 'get_oposicion')
    list_filter = ('capitulo__tema__oposiciones',)
    search_fields = ('numero', 'contenido', 'capitulo__titulo', 'capitulo__tema__titulo')
    autocomplete_fields = ['capitulo']
    inlines = [PreguntaInline]

    @admin.display(description='Capítulo')
    def get_capitulo(self, obj):
        return obj.capitulo.titulo

    @admin.display(description='Tema')
    def get_tema(self, obj):
        return obj.capitulo.tema.titulo

    @admin.display(description='Oposición')
    def get_oposicion(self, obj):
        oposiciones = obj.capitulo.tema.oposiciones.all()
        return ", ".join(o.nombre for o in oposiciones)


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = (
        'enunciado_corto', 'respuesta_correcta',
        'get_articulo', 'get_capitulo', 'get_tema',
    )
    list_filter = (
        'respuesta_correcta',
        'articulo__capitulo__tema__oposiciones',
        'articulo__capitulo__tema',
    )
    search_fields = (
        'enunciado', 'respuesta_a', 'respuesta_b', 'respuesta_c', 'respuesta_d',
        'articulo__numero', 'articulo__capitulo__titulo',
    )
    # ✅ Clave: reemplaza el <select> enorme por un widget de búsqueda
    autocomplete_fields = ['articulo']
    readonly_fields = ('get_articulo_preview',)
    fieldsets = (
        ('Referencia', {
            'fields': ('articulo', 'get_articulo_preview'),
            'description': (
                'Selecciona el artículo al que hace referencia esta pregunta. '
                'Usa el buscador: escribe el número o parte del capítulo para filtrar.'
            ),
        }),
        ('Enunciado y Respuestas', {
            'fields': (
                'enunciado',
                'respuesta_a', 'respuesta_b', 'respuesta_c', 'respuesta_d',
                'respuesta_correcta',
            ),
        }),
        ('Explicación Opcional', {
            'fields': ('explicacion',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Enunciado')
    def enunciado_corto(self, obj):
        return obj.enunciado[:80] + '…' if len(obj.enunciado) > 80 else obj.enunciado

    @admin.display(description='Artículo')
    def get_articulo(self, obj):
        return f"Art. {obj.articulo.numero}"

    @admin.display(description='Capítulo')
    def get_capitulo(self, obj):
        return obj.articulo.capitulo.titulo[:50]

    @admin.display(description='Tema')
    def get_tema(self, obj):
        return obj.articulo.capitulo.tema.titulo[:50]

    @admin.display(description='Contenido del artículo seleccionado')
    def get_articulo_preview(self, obj):
        if obj.articulo_id:
            return format_html(
                '<div style="background:#f8f9fa;padding:10px;border-radius:6px;'
                'border-left:4px solid #0d4c83;max-height:150px;overflow-y:auto;">'
                '<strong>Capítulo:</strong> {}<br>'
                '<strong>Tema:</strong> {}<br/><hr>'
                '<small>{}</small></div>',
                obj.articulo.capitulo.titulo,
                obj.articulo.capitulo.tema.titulo,
                obj.articulo.contenido[:500] + ('…' if len(obj.articulo.contenido) > 500 else ''),
            )
        return "Selecciona un artículo para ver su contenido."


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


@admin.register(NotaEstudio)
class NotaEstudioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'capitulo', 'fecha_actualizacion')
    list_filter = ('capitulo__tema__oposiciones',)
    search_fields = ('usuario__email', 'contenido')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nombre_completo', 'oposicion_activa')
    list_filter = ('oposicion_activa',)
    search_fields = ('usuario__email', 'nombre', 'apellidos')


@admin.register(ProgresoEstudio)
class ProgresoEstudioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'capitulo', 'completado', 'fecha_completado')
    list_filter = ('completado', 'capitulo__tema__oposiciones')
    search_fields = ('usuario__email', 'capitulo__titulo')


@admin.register(RecursoTema)
class RecursoTemaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'capitulo')
    list_filter = ('tipo', 'capitulo__tema__oposiciones')
    search_fields = ('titulo', 'capitulo__titulo')


# ── Cabecera del panel ────────────────────────────────────────────────────────
admin.site.site_header = 'Panel de Administración — OPOSICIONES'
admin.site.index_title = 'Gestión de contenido y usuarios'
admin.site.site_title = 'Admin Oposiciones'
