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
    Tema, Capitulo, Oposicion,
    Examen, Pregunta, RespuestaUsuario, Articulo, NotaEstudio, PerfilUsuario
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

        # ── Oposición Activa ──────────────────────────────────────────────────
        perfil = getattr(usuario, 'perfil', None)
        oposicion_activa = perfil.oposicion_activa if perfil else None

        # ── KPIs globales (solo de su oposición activa si existe) ─────────────
        examenes_qs = Examen.objects.filter(usuario=usuario, puntuacion__isnull=False)
        if oposicion_activa:
            examenes_qs = examenes_qs.filter(oposicion=oposicion_activa)
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

        # ── Rendimiento por Tema (Oposición Activa) ────────────────────────────
        rendimiento_por_tema = []
        temas_a_evaluar = Tema.objects.filter(oposiciones=oposicion_activa) if oposicion_activa else Tema.objects.all()
        
        for tema in temas_a_evaluar:
            resps_tema = todas_respuestas.filter(
                pregunta__articulo__capitulo__tema=tema
            )
            total_tema = resps_tema.count()
            if total_tema > 0:
                aciertos_tema = resps_tema.filter(es_correcta=True).count()
                pct = round((aciertos_tema / total_tema) * 100)
                rendimiento_por_tema.append({
                    'nombre': tema.titulo[:35],
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

        # ── Recomendaciones Diarias (Coach de Estudio) ─────────────────────────
        recomendaciones = []
        capitulos_evaluar = Capitulo.objects.filter(tema__oposiciones=oposicion_activa).distinct() if oposicion_activa else Capitulo.objects.all()
        
        hoy = timezone.now()
        for capitulo in capitulos_evaluar:
            resps_cap = RespuestaUsuario.objects.filter(
                examen__usuario=usuario,
                pregunta__articulo__capitulo=capitulo
            )
            
            total_resp = resps_cap.count()
            score = 0.0
            
            if total_resp > 0:
                fallos = resps_cap.filter(es_correcta=False).count()
                pct_fallo = (fallos / total_resp) * 100.0
                
                ultimo_acierto = resps_cap.filter(es_correcta=True).order_by('-examen__fecha_finalizacion').first()
                if ultimo_acierto:
                    dias_sin_acierto = (hoy - ultimo_acierto.examen.fecha_finalizacion).days
                else:
                    dias_sin_acierto = 30
                    
                olvido_normalizado = min(dias_sin_acierto / 30.0, 1.0) * 100.0
                score = (pct_fallo * 0.6) + (olvido_normalizado * 0.4)
            else:
                score = 40.0 # Ligera prioridad a lo inexplorado
                
            recomendaciones.append({
                'capitulo': capitulo,
                'score': score
            })
            
        recomendaciones.sort(key=lambda x: x['score'], reverse=True)
        top_recomendaciones = recomendaciones[:3]

        context.update({
            'oposicion_activa': oposicion_activa,
            'total_examenes': total_examenes,
            'puntuacion_media': puntuacion_media,
            'puntuacion_maxima': puntuacion_maxima,
            'acierto_global_pct': acierto_global_pct,
            'chart_labels': json.dumps(chart_labels),
            'chart_data': json.dumps(chart_data),
            'ultimos_examenes': ultimos_examenes,
            'rendimiento_por_tema': rendimiento_por_tema,
            'preguntas_urgentes': preguntas_urgentes,
            'recomendaciones_estudio': top_recomendaciones,
        })
        return context


class TemarioView(LoginRequiredMixin, ListView):
    """Lista el temario filtrado por la oposicion activa del usuario."""

    template_name = 'examen/temario.html'
    model = Tema
    context_object_name = 'temas'
    ordering = ['bloque', 'orden', 'titulo']

    def get_queryset(self):
        qs = super().get_queryset()
        perfil = getattr(self.request.user, 'perfil', None)
        if perfil and perfil.oposicion_activa:
            qs = qs.filter(oposiciones=perfil.oposicion_activa)
        return qs


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

@login_required
def descargar_tema(request, pk):
    """Descarga el archivo de documentación de un Tema si existe."""
    tema = get_object_or_404(Tema, pk=pk)

    if tema.documentacion and hasattr(tema.documentacion, 'path'):
        tema_path = tema.documentacion.path
        response = FileResponse(
            open(tema_path, 'rb'),
            as_attachment=True,
            filename=tema.documentacion.name,
        )
        if not settings.DEBUG:
            response['Connection'] = 'close'
        return response

    return redirect(
        reverse('examen:errores', kwargs={'error_code': 404})
        + '?mensaje=No+se+encontr%C3%B3+el+archivo+de+documentaci%C3%B3n+del+tema'
    )

class SelectorOposicionView(LoginRequiredMixin, View):
    """Permite al usuario cambiar a otra de sus oposiciones inscritas activas."""
    
    def post(self, request, pk, *args, **kwargs):
        oposicion_nueva = get_object_or_404(Oposicion, pk=pk)
        perfil = getattr(request.user, 'perfil', None)
        
        # Opcional: Proteger para que solo pueda elegir una a la que está inscrito
        if perfil and oposicion_nueva in perfil.oposiciones_inscritas.all():
            perfil.oposicion_activa = oposicion_nueva
            perfil.save(update_fields=['oposicion_activa'])
            
        next_url = request.POST.get('next', reverse('examen:home'))
        return redirect(next_url)

class CapituloDetalleView(LoginRequiredMixin, DetailView):
    """Vista de lectura profunda de los Artículos de un Capítulo y panel de Notas."""
    
    model = Capitulo
    template_name = 'examen/capitulo_detalle.html'
    context_object_name = 'capitulo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        capitulo = self.object
        
        # Obtener los artículos ordenados
        context['articulos'] = capitulo.articulosCapitulo.all().order_by('numero')
        
        # Recuperar nota si existe
        nota_qs = NotaEstudio.objects.filter(usuario=self.request.user, capitulo=capitulo)
        context['nota_estudio'] = nota_qs.first() if nota_qs.exists() else None

        # Lógica de Siguiente y Anterior dentro del mismo Tema
        todos_capitulos_mismo_tema = list(Capitulo.objects.filter(tema=capitulo.tema).order_by('orden'))
        
        try:
            current_index = todos_capitulos_mismo_tema.index(capitulo)
            context['capitulo_anterior'] = todos_capitulos_mismo_tema[current_index - 1] if current_index > 0 else None
            context['capitulo_siguiente'] = todos_capitulos_mismo_tema[current_index + 1] if current_index < len(todos_capitulos_mismo_tema) - 1 else None
        except ValueError:
            context['capitulo_anterior'] = None
            context['capitulo_siguiente'] = None
            
        return context


class GuardarNotaView(LoginRequiredMixin, View):
    """Guarda vía POST el contenido del textarea de Notas de un capítulo."""
    
    def post(self, request, pk, *args, **kwargs):
        capitulo = get_object_or_404(Capitulo, pk=pk)
        contenido = request.POST.get('contenido', '').strip()
        
        if contenido:
            NotaEstudio.objects.update_or_create(
                usuario=request.user,
                capitulo=capitulo,
                defaults={'contenido': contenido}
            )
        else:
            # Si el usuario envía en blanco, la borramos para mantener la BD limpia
            NotaEstudio.objects.filter(usuario=request.user, capitulo=capitulo).delete()
            
        return redirect(reverse('examen:capitulo_detalle', kwargs={'pk': capitulo.pk}))


class StartExamenCapituloView(LoginRequiredMixin, View):
    """Crea un simulacro exclusivo con preguntas de un capítulo concreto."""

    def post(self, request, pk, *args, **kwargs):
        capitulo = get_object_or_404(Capitulo, pk=pk)
        
        # Obtener todas las preguntas del capítulo
        preguntas = list(Pregunta.objects.filter(articulo__capitulo=capitulo).order_by('?'))
        
        if not preguntas:
            # Podríamos redirigir con un mensaje de error si el capítulo no tiene preguntas aún
            url = reverse('examen:capitulo_detalle', kwargs={'pk': capitulo.pk})
            return redirect(f"{url}?error=sin_preguntas")

        # Configurar el examen
        examen = Examen.objects.create(
            usuario=request.user,
            tipo=Examen.TipoExamen.CAPITULO
        )

        primera_oposicion = Oposicion.objects.first()
        if primera_oposicion:
            examen.oposicion = primera_oposicion
            examen.save(update_fields=['oposicion'])

        # Solo le ponemos las preguntas de este capítulo
        examen.preguntas.set(preguntas[:primera_oposicion.num_preguntas if primera_oposicion else 100])
        
        logger.info(
            'Examen de Capítulo #%d iniciado por %s con %d preguntas.',
            examen.pk, request.user.email, min(len(preguntas), 100)
        )
        return redirect(reverse('examen:simulacion_pagina', kwargs={'examen_id': examen.id}))


class StartExamenView(LoginRequiredMixin, View):
    """
    Crea un nuevo examen para el usuario, selecciona preguntas al azar
    según la configuración de la oposición, y redirige a la primera página.
    """

    def post(self, request, *args, **kwargs):
        examen = Examen.objects.create(usuario=request.user)

        # ── Setup Oposición Activa ────────────────────────────────────────────
        perfil = getattr(request.user, 'perfil', None)
        oposicion_activa = perfil.oposicion_activa if perfil else Oposicion.objects.first()
        
        num_preguntas = 100
        if oposicion_activa:
            num_preguntas = oposicion_activa.num_preguntas
            examen.oposicion = oposicion_activa
            examen.save(update_fields=['oposicion'])

        # ── Pool de Preguntas de esta Oposición ───────────────────────────────
        preguntas_base = Pregunta.objects.all()
        if oposicion_activa:
            preguntas_base = preguntas_base.filter(articulo__capitulo__tema__oposiciones=oposicion_activa)

        # --- Algoritmo Adaptativo 40/30/30 ---
        preguntas_finales = []
        user_resps = RespuestaUsuario.objects.filter(examen__usuario=request.user)

        # 1. 40% Preguntas Falladas (Prioridad Absoluta)
        meta_falladas = int(num_preguntas * 0.40)
        preguntas_falladas_ids = list(
            user_resps.filter(es_correcta=False)
            .values_list('pregunta_id', flat=True)
            .distinct()
        )
        falladas = list(preguntas_base.filter(id__in=preguntas_falladas_ids).order_by('?')[:meta_falladas])
        preguntas_finales.extend(falladas)

        huecos_restantes = num_preguntas - len(preguntas_finales)

        # 2. 30% Preguntas Olvidadas (Acertadas hace mucho tiempo)
        meta_olvidadas = min(int(num_preguntas * 0.30), huecos_restantes)
        if meta_olvidadas > 0:
            preguntas_acertadas_ids = list(
                user_resps.filter(es_correcta=True)
                .exclude(pregunta_id__in=[p.id for p in preguntas_finales])
                .order_by('examen__fecha_finalizacion')  # Las más antiguas primero
                .values_list('pregunta_id', flat=True)
                .distinct()
            )
            olvidadas_ids = []
            vistos = set()
            for pid in preguntas_acertadas_ids:
                if pid not in vistos:
                    olvidadas_ids.append(pid)
                    vistos.add(pid)
                    if len(olvidadas_ids) >= meta_olvidadas:
                        break
            
            olvidadas = list(preguntas_base.filter(id__in=olvidadas_ids))
            preguntas_finales.extend(olvidadas)

        huecos_restantes = num_preguntas - len(preguntas_finales)

        # 3. 30% Preguntas Nuevas (o rellenar los huecos que falten)
        respondidas_total_ids = list(user_resps.values_list('pregunta_id', flat=True).distinct())
        nuevas = list(
            preguntas_base.exclude(id__in=respondidas_total_ids)
            .order_by('?')[:huecos_restantes]
        )
        preguntas_finales.extend(nuevas)

        huecos_restantes = num_preguntas - len(preguntas_finales)

        # 4. Fallback de Seguridad
        if huecos_restantes > 0:
            ids_actuales = [p.id for p in preguntas_finales]
            relleno = list(preguntas_base.exclude(id__in=ids_actuales).order_by('?')[:huecos_restantes])
            preguntas_finales.extend(relleno)

        # Guardamos la relación
        examen.preguntas.set(preguntas_finales)

        logger.info(
            'Examen #%d Adaptativo iniciado por %s. Total seleccionadas: %d (F:%d, O:%d, N:%d, R:%d).',
            examen.pk, request.user.email, len(preguntas_finales),
            len(falladas), len(olvidadas) if 'olvidadas' in locals() else 0,
            len(nuevas), huecos_restantes if huecos_restantes > 0 and 'relleno' in locals() else 0
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
