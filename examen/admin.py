from django.contrib import admin
from .models import Oposicion, Bloque, Tema, Capitulo, Articulo, Pregunta, Examen

# Define un 'inline' para los capítulos
@admin.register(Oposicion)
class OposicionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')

    
@admin.register(Bloque)
class BloqueAdmin(admin.ModelAdmin):
    list_display = ('orden', 'titulo')
    ordering = ('orden',)



class CapituloInline(admin.TabularInline): # O StackedInline
    model = Capitulo
    extra = 1 # Cuántos formularios de capítulo en blanco mostrar


@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'orden')
    # ¡Aquí está la magia!
    inlines = [CapituloInline]


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('enunciado', 'respuesta_correcta', 'articulo')

admin.site.site_header = 'Panel de control OPOSICIONES'
admin.site.index_title = 'Administración OPOSICIONES'
admin.site.site_title = 'Admin OPOSICIONES'

# ... registrar el resto de modelos ...
admin.site.register(Capitulo)
