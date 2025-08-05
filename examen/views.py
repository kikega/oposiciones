# Django
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView, ListView, DetailView
from django.urls import reverse
from django.http import FileResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator
from django.utils import timezone

# Librerias Python
from decimal import Decimal, ROUND_HALF_UP

# De Examen
from .models import Tema, Examen, Pregunta, RespuestaUsuario, Capitulo

# Variables globales
# Número de preguntas por página
PREGUNTAS_POR_PAGINA = 10
# Penalización por error
PENALIZACION_POR_ERROR = Decimal(0.33)


# Create your views here.
class HomeView(LoginRequiredMixin, TemplateView):
    """Home de la aplicación"""
    template_name = 'examen/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


class TemarioView(LoginRequiredMixin, ListView):
    """Lista el temario de la oposicion"""

    template_name = 'examen/temario.html'
    model = Tema
    context_object_name = 'temas'
    ordering = ['orden']


class TemarioDetalleView(LoginRequiredMixin, TemplateView):
    """Detalle de un tema en particular"""

    template_name = 'examen/temario_detalle.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tema = get_object_or_404(Tema, pk=kwargs['pk'])
        context['tema'] = tema
        capitulos = Capitulo.objects.filter(tema=tema).order_by('orden')
        context['capitulos'] = capitulos

        return context

@login_required
def descargar_capitulo(request, pk):
    capitulo = get_object_or_404(Capitulo, pk=pk)

    if capitulo.documentacion and hasattr(capitulo.documentacion, 'path'):
        # Obtener la ruta absoluta al archivo
        # capitulo.documentacion.path te da la ruta absoluta si MEDIA_ROOT está bien configurado
        capitulo_path = capitulo.documentacion.path
        # Abrir el archivo en modo binario para lectura
        response = FileResponse(open(capitulo_path, 'rb'), as_attachment=True, filename=capitulo.documentacion.name)
        # as_attachment=True: Fuerza la descarga.
        # filename=capitulo.documentacion.name: Sugiere el nombre original del archivo al navegador.
        # Django se encarga de las cabeceras Content-Type, Content-Disposition,
        if not settings.DEBUG: # Solo añadir en producción
            response['Connection'] = 'close'
        return response
    else:
        return redirect("examen:error", error_code=404, error_message="No se encontró el archivo de la documentacion")

class StartExamenView(LoginRequiredMixin, View):
    """
    Vista para iniciar una nueva simulación de examen.
    Crea el objeto Examen, selecciona 100 preguntas al azar y redirige a la primera página.
    """
    def post(self, request, *args, **kwargs):
        # Crear un nuevo objeto Examen para el usuario logueado
        examen = Examen.objects.create(usuario=request.user)

        # Seleccionar 100 preguntas al azar de la base de datos
        # order_by('?') es funcional pero puede ser lento en BBDD muy grandes (PostgreSQL es más eficiente)
        preguntas_aleatorias = Pregunta.objects.all().order_by('?')[:100]
        print(f'Preguntas seleccionadas: {preguntas_aleatorias.count()}')

        # Añadir las preguntas al examen
        examen.preguntas.set(preguntas_aleatorias)
        print('Preguntas añadidas al examen')

        # Redirigir a la primera página de la simulación
        return redirect(reverse('examen:simulacion_pagina', kwargs={'examen_id': examen.id}))

class SimulacionView(LoginRequiredMixin, View):
    """
    Vista principal para realizar el examen, página por página.
    """

    template_name = 'examen/simulacion_pagina.html'

    def get(self, request, examen_id):
        examen = get_object_or_404(Examen, id=examen_id, usuario=request.user)

        # Si el examen ya está finalizado, no se puede continuar. Redirigir a resultados.
        if examen.fecha_finalizacion:
            return redirect(reverse('examen:simulacion_resultados', kwargs={'examen_id': examen.id}))

        # Usamos Paginator de Django para manejar las páginas de preguntas
        paginator = Paginator(examen.preguntas.all(), PREGUNTAS_POR_PAGINA)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context = {
            'examen': examen,
            'page_obj': page_obj,
            'total_preguntas': paginator.count
        }
        return render(request, self.template_name, context)

    def post(self, request, examen_id):
        examen = get_object_or_404(Examen, id=examen_id, usuario=request.user)

        # Procesar las respuestas enviadas en el formulario
        for key, value in request.POST.items():
            if key.startswith('pregunta_'):
                pregunta_id = int(key.split('_')[1])
                pregunta = Pregunta.objects.get(id=pregunta_id)

                # Crear o actualizar la respuesta del usuario
                RespuestaUsuario.objects.update_or_create(
                    examen=examen,
                    pregunta=pregunta,
                    defaults={'respuesta_seleccionada': value}
                )

        # Determinar a dónde ir después
        paginator = Paginator(examen.preguntas.all(), PREGUNTAS_POR_PAGINA)
        current_page_number = int(request.POST.get('page_number', 1))
        page_obj = paginator.get_page(current_page_number)

        if page_obj.has_next():
            # Si hay una página siguiente, redirigir a ella
            next_page_url = f"{reverse('examen:simulacion_pagina', kwargs={'examen_id': examen.id})}?page={page_obj.next_page_number()}"
            return redirect(next_page_url)
        else:
            # Si es la última página, finalizar el examen y redirigir a los resultados
            return redirect(reverse('examen:simulacion_resultados', kwargs={'examen_id': examen.id}))

class ResultadosView(LoginRequiredMixin, DetailView):
    """
    Muestra los resultados finales de un examen.
    Si el examen no está calculado, lo calcula antes de mostrarlo.
    """
    model = Examen
    template_name = 'examen/simulacion_resultados.html'
    context_object_name = 'examen'
    pk_url_kwarg = 'examen_id' # Para que coincida con la URL

    def get_object(self, queryset=None):
        # Obtenemos el examen y nos aseguramos de que pertenece al usuario
        examen = super().get_object(queryset)
        if examen.usuario != self.request.user:
            from django.http import Http404
            raise Http404("Examen no encontrado")

        # Si el examen no tiene puntuación, la calculamos ahora
        if examen.puntuacion is None:
            self.calcular_y_guardar_puntuacion(examen)

        return examen

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        examen = self.object

        respuestas = examen.respuestas_usuario.all()
        aciertos = respuestas.filter(es_correcta=True).count()
        errores = respuestas.filter(es_correcta=False).count()
        sin_contestar = examen.preguntas.count() - (aciertos + errores)

        context['aciertos'] = aciertos
        context['errores'] = errores
        context['sin_contestar'] = sin_contestar
        context['preguntas_falladas'] = respuestas.filter(es_correcta=False).select_related('pregunta', 'pregunta__capitulo')

        return context

    def calcular_y_guardar_puntuacion(self, examen):
        aciertos = examen.respuestas_usuario.filter(es_correcta=True).count()
        errores = examen.respuestas_usuario.filter(es_correcta=False).count()

        # Usamos Decimal para precisión
        puntuacion_aciertos = Decimal(aciertos)
        penalizacion = Decimal(errores) * PENALIZACION_POR_ERROR

        puntuacion_final = puntuacion_aciertos - penalizacion

        # Actualizar el objeto Examen en la base de datos
        examen.puntuacion = puntuacion_final
        examen.fecha_finalizacion = timezone.now()
        examen.save()

class ErrorView(LoginRequiredMixin, TemplateView):
    """Errores de la aplicación"""

    template_name = 'examen/error.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['error_code'] = kwargs['error_code']
        context['error_message'] = kwargs['error_message']

        return context
