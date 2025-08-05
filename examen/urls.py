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
    path("descargar/<int:pk>/", examen_views.descargar_capitulo, name="descargar_capitulo"),
    path("simulacion/", examen_views.StartExamenView.as_view(), name="simular_examen"),
    # URL principal para hacer el examen. Recibe el ID del examen
    path('simulacion/<int:examen_id>/', examen_views.SimulacionView.as_view(), name='simulacion_pagina'),
    # URL para ver los resultados finales
    path('simulacion/<int:examen_id>/resultados/', examen_views.ResultadosView.as_view(), name='simulacion_resultados'),
    path("error/<int:error_code>/", examen_views.ErrorView.as_view(), name="errores"),
]
