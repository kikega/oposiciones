from django.contrib import admin
from .models import Tema, Capitulo, Pregunta, Examen

# Define un 'inline' para los capítulos
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
    list_display = ('enunciado', 'respuesta_correcta', 'capitulo')

admin.site.site_header = 'Panel de control OPOSICIONES'
admin.site.index_title = 'Administración OPOSICIONES'
admin.site.site_title = 'Admin OPOSICIONES'

# ... registrar el resto de modelos ...
admin.site.register(Capitulo)
