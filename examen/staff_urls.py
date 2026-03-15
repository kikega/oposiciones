"""URLs del panel de carga de datos — exclusivo para usuarios staff."""

from django.urls import path
from examen import views as examen_views

app_name = 'staff'

urlpatterns = [
    # ── Dashboard del panel ───────────────────────────────────────────────────
    path('', examen_views.PanelStaffView.as_view(), name='panel'),

    # ── Gestión de preguntas ──────────────────────────────────────────────────
    path('preguntas/nueva/', examen_views.NuevaPreguntaStaffView.as_view(), name='nueva_pregunta'),

    # ── APIs JSON para selects en cascada ─────────────────────────────────────
    path('api/temas/', examen_views.ApiTemasPorOposicionView.as_view(), name='api_temas'),
    path('api/capitulos/', examen_views.ApiCapitulosPorTemaView.as_view(), name='api_capitulos'),
    path('api/articulos/', examen_views.ApiArticulosPorCapituloView.as_view(), name='api_articulos'),
]
