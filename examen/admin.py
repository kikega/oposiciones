from django.contrib import admin
from .models import Tema, Capitulo, Pregunta, Examen, RespuestaUsuario

# Define un 'inline' para los capítulos
class CapituloInline(admin.TabularInline): # O StackedInline
    model = Capitulo
    extra = 1 # Cuántos formularios de capítulo en blanco mostrar

@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'orden')
    # ¡Aquí está la magia!
    inlines = [CapituloInline]

# ... registrar el resto de modelos ...
admin.site.register(Capitulo)
admin.site.register(Pregunta)

