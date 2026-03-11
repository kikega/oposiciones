"""Configuración URLs de examen"""

# Django
from django.urls import path

# App usuarios
from examen import views as examen_views

# Asegúrate de tener un namespace
app_name = 'examen'

urlpatterns = [
    path("temario/", examen_views.TemarioView.as_view(), name="temario"),
    path("temario/<int:pk>/", examen_views.TemarioDetalleView.as_view(), name="temario_detalle"),
    path("capitulo/<int:pk>/", examen_views.CapituloDetalleView.as_view(), name="capitulo_detalle"),
    path("capitulo/<int:pk>/nota/", examen_views.GuardarNotaView.as_view(), name="guardar_nota"),
    path("capitulo/<int:pk>/simulacro/", examen_views.StartExamenCapituloView.as_view(), name="simular_examen_capitulo"),
    path("descargar/<int:pk>/", examen_views.descargar_capitulo, name="descargar_capitulo"),
    path("descargar/tema/<int:pk>/", examen_views.descargar_tema, name="descargar_tema"),
    path("simulacion/", examen_views.StartExamenView.as_view(), name="simular_examen"),
    # URL principal para hacer el examen. Recibe el ID del examen
    path('simulacion/<int:examen_id>/', examen_views.SimulacionView.as_view(), name='simulacion_pagina'),
    # URL para ver los resultados finales
    path('simulacion/<int:examen_id>/resultados/', examen_views.ResultadosView.as_view(), name='simulacion_resultados'),
    path("seleccionar-oposicion/<int:pk>/", examen_views.SelectorOposicionView.as_view(), name="seleccionar_oposicion"),
    path("error/<int:error_code>/", examen_views.ErrorView.as_view(), name="errores"),
    # El mensaje de error se pasa como query param: ?mensaje=...
]
