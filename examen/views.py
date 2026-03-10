"""Vistas de la aplicación examen."""

import json
import logging
from decimal import Decimal

# Django
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView, ListView, DetailView
from django.urls import reverse
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Max, Min, Avg, Count

# De Examen
from .models import (
    Bloque, Tema, Capitulo, Oposicion,
    Examen, Pregunta, RespuestaUsuario,
)

logger = logging.getLogger(__name__)

# Número de preguntas por página en la simulación
PREGUNTAS_POR_PAGINA = 10


class HomeView(LoginRequiredMixin, TemplateView):
    """Dashboard principal con estadísticas reales del usuario."""

    template_name = 'examen/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user

        # ── KPIs globales ─────────────────────────────────────────────────────
        examenes_qs = Examen.objects.filter(
            usuario=usuario, puntuacion__isnull=False
        )
        total_examenes = examenes_qs.count()

        stats = examenes_qs.aggregate(
            media=Avg('puntuacion'),
            maxima=Max('puntuacion'),
        )
        puntuacion_media = round(stats['media'] or 0, 2)
        puntuacion_maxima = round(stats['maxima'] or 0, 2)

        # Acierto global (sobre todas las respuestas dadas)
        todas_respuestas = RespuestaUsuario.objects.filter(examen__usuario=usuario)
        total_resp = todas_respuestas.count()
        aciertos_resp = todas_respuestas.filter(es_correcta=True).count()
        acierto_global_pct = round((aciertos_resp / total_resp) * 100, 1) if total_resp > 0 else 0

        # ── Datos para el gráfico Chart.js (últimos 20 exámenes completados) ──
        examenes_chart = list(
            examenes_qs.order_by('fecha_finalizacion')
            .values('fecha_finalizacion', 'puntuacion')
        )
        chart_labels = [
            e['fecha_finalizacion'].strftime('%d/%m') for e in examenes_chart
        ]
        chart_data = [round(float(e['puntuacion']), 2) for e in examenes_chart]

        # ── Últimos 10 exámenes ────────────────────────────────────────────────
        ultimos_examenes = examenes_qs.select_related('oposicion').order_by(
            '-fecha_finalizacion'
        )[:10]

        # ── Rendimiento por Bloque ─────────────────────────────────────────────
        rendimiento_por_tema = []
        for bloque in Bloque.objects.all():
            resps_bloque = todas_respuestas.filter(
                pregunta__articulo__capitulo__tema__bloque=bloque
            )
            total_bloque = resps_bloque.count()
            if total_bloque > 0:
                aciertos_bloque = resps_bloque.filter(es_correcta=True).count()
                pct = round((aciertos_bloque / total_bloque) * 100)
                rendimiento_por_tema.append({
                    'nombre': bloque.titulo[:35],
                    'pct': pct,
                    'clase': 'success' if pct >= 75 else ('warning' if pct >= 50 else 'danger'),
                })
        rendimiento_por_tema.sort(key=lambda x: x['pct'])

        # ── Preguntas urgentes: las más falladas por este usuario ──────────────
        preguntas_urgentes = (
            RespuestaUsuario.objects
            .filter(examen__usuario=usuario, es_correcta=False)
            .values(
                'pregunta__enunciado',
                'pregunta__articulo__capitulo__titulo',
            )
            .annotate(veces_fallada=Count('id'))
            .order_by('-veces_fallada')[:5]
        )

        context.update({
            'total_examenes': total_examenes,
            'puntuacion_media': puntuacion_media,
            'puntuacion_maxima': puntuacion_maxima,
            'acierto_global_pct': acierto_global_pct,
            'chart_labels': json.dumps(chart_labels),
            'chart_data': json.dumps(chart_data),
            'ultimos_examenes': ultimos_examenes,
            'rendimiento_por_tema': rendimiento_por_tema,
            'preguntas_urgentes': preguntas_urgentes,
        })
        return context


class TemarioView(LoginRequiredMixin, ListView):
    """Lista el temario de la oposicion."""

    template_name = 'examen/temario.html'
    model = Tema
    context_object_name = 'temas'
    ordering = ['bloque__orden', 'orden']


class TemarioDetalleView(LoginRequiredMixin, TemplateView):
    """Detalle de un tema en particular."""

    template_name = 'examen/temario_detalle.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tema = get_object_or_404(Tema, pk=kwargs['pk'])
        context['tema'] = tema
        context['capitulos'] = Capitulo.objects.filter(tema=tema).order_by('orden')
        return context


@login_required
def descargar_capitulo(request, pk):
    """Descarga el archivo de documentación de un capítulo."""
    capitulo = get_object_or_404(Capitulo, pk=pk)

    if capitulo.documentacion and hasattr(capitulo.documentacion, 'path'):
        capitulo_path = capitulo.documentacion.path
        response = FileResponse(
            open(capitulo_path, 'rb'),
            as_attachment=True,
            filename=capitulo.documentacion.name,
        )
        if not settings.DEBUG:
            response['Connection'] = 'close'
        return response

    return redirect(
        reverse('examen:errores', kwargs={'error_code': 404})
        + '?mensaje=No+se+encontr%C3%B3+el+archivo+de+documentaci%C3%B3n'
    )


class StartExamenView(LoginRequiredMixin, View):
    """
    Crea un nuevo examen para el usuario, selecciona preguntas al azar
    según la configuración de la oposición, y redirige a la primera página.
    """

    def post(self, request, *args, **kwargs):
        examen = Examen.objects.create(usuario=request.user)

        # Usar configuración de la primera oposición si existe
        num_preguntas = 100
        primera_oposicion = Oposicion.objects.first()
        if primera_oposicion:
            num_preguntas = primera_oposicion.num_preguntas
            examen.oposicion = primera_oposicion
            examen.save(update_fields=['oposicion'])

        preguntas_aleatorias = Pregunta.objects.all().order_by('?')[:num_preguntas]
        examen.preguntas.set(preguntas_aleatorias)

        logger.info(
            'Examen #%d iniciado por %s con %d preguntas.',
            examen.pk, request.user.email, preguntas_aleatorias.count()
        )
        return redirect(reverse('examen:simulacion_pagina', kwargs={'examen_id': examen.id}))


class SimulacionView(LoginRequiredMixin, View):
    """Vista principal para realizar el examen, página por página."""

    template_name = 'examen/simulacion_pagina.html'

    def get(self, request, examen_id):
        examen = get_object_or_404(Examen, id=examen_id, usuario=request.user)

        if examen.fecha_finalizacion:
            return redirect(reverse('examen:simulacion_resultados', kwargs={'examen_id': examen.id}))

        paginator = Paginator(examen.preguntas.all(), PREGUNTAS_POR_PAGINA)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Precargar respuestas ya guardadas para marcar radio buttons
        respuestas_guardadas = {
            r.pregunta_id: r.respuesta_seleccionada
            for r in examen.respuestas_usuario.filter(
                pregunta__in=page_obj.object_list
            )
        }

        context = {
            'examen': examen,
            'page_obj': page_obj,
            'total_preguntas': paginator.count,
            'respuestas_guardadas': respuestas_guardadas,
        }
        return render(request, self.template_name, context)

    def post(self, request, examen_id):
        examen = get_object_or_404(Examen, id=examen_id, usuario=request.user)

        for key, value in request.POST.items():
            if key.startswith('pregunta_'):
                try:
                    pregunta_id = int(key.split('_')[1])
                    pregunta = Pregunta.objects.get(id=pregunta_id)
                    RespuestaUsuario.objects.update_or_create(
                        examen=examen,
                        pregunta=pregunta,
                        defaults={'respuesta_seleccionada': value},
                    )
                except (ValueError, Pregunta.DoesNotExist):
                    logger.warning('Respuesta inválida ignorada: key=%s', key)

        paginator = Paginator(examen.preguntas.all(), PREGUNTAS_POR_PAGINA)
        current_page_number = int(request.POST.get('page_number', 1))
        page_obj = paginator.get_page(current_page_number)

        if page_obj.has_next():
            next_url = (
                reverse('examen:simulacion_pagina', kwargs={'examen_id': examen.id})
                + f'?page={page_obj.next_page_number()}'
            )
            return redirect(next_url)

        return redirect(reverse('examen:simulacion_resultados', kwargs={'examen_id': examen.id}))


class ResultadosView(LoginRequiredMixin, DetailView):
    """Muestra los resultados finales de un examen y calcula la puntuación si aún no existe."""

    model = Examen
    template_name = 'examen/simulacion_resultados.html'
    context_object_name = 'examen'
    pk_url_kwarg = 'examen_id'

    def get_object(self, queryset=None):
        examen = super().get_object(queryset)
        if examen.usuario != self.request.user:
            raise Http404("Examen no encontrado.")
        if examen.puntuacion is None:
            self._calcular_y_guardar_puntuacion(examen)
        return examen

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        examen = self.object

        respuestas = examen.respuestas_usuario.select_related(
            'pregunta',
            'pregunta__articulo',
            'pregunta__articulo__capitulo',
        ).all()

        aciertos = respuestas.filter(es_correcta=True).count()
        errores = respuestas.filter(es_correcta=False).count()
        sin_contestar = examen.preguntas.count() - (aciertos + errores)

        context.update({
            'aciertos': aciertos,
            'errores': errores,
            'sin_contestar': sin_contestar,
            'preguntas_falladas': respuestas.filter(es_correcta=False),
        })
        return context

    def _calcular_y_guardar_puntuacion(self, examen: Examen) -> None:
        """Calcula la puntuación aplicando penalización por error según la oposición."""
        aciertos = examen.respuestas_usuario.filter(es_correcta=True).count()
        errores = examen.respuestas_usuario.filter(es_correcta=False).count()

        penalizacion = (
            examen.oposicion.penalizacion
            if examen.oposicion
            else Decimal('0.33')
        )

        puntuacion_final = Decimal(aciertos) - (Decimal(errores) * penalizacion)

        examen.puntuacion = float(puntuacion_final)
        examen.respuestas_correctas = aciertos
        examen.respuestas_erroneas = errores
        examen.fecha_finalizacion = timezone.now()
        examen.save()

        logger.info(
            'Examen #%d finalizado. Puntuación: %.2f (aciertos=%d, errores=%d)',
            examen.pk, float(puntuacion_final), aciertos, errores
        )


class ErrorView(LoginRequiredMixin, TemplateView):
    """Página de error de la aplicación."""

    template_name = 'examen/error.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['error_code'] = kwargs.get('error_code', 500)
        context['error_message'] = self.request.GET.get('mensaje', 'Se ha producido un error inesperado.')
        return context
