# Los modelos Examen y RespuestaUsuario no necesitan cambios.
# Siguen refiriéndose a Pregunta, y a través de Pregunta podemos llegar
# al Capítulo y al Tema para las estadísticas.
# Por ejemplo: respuesta_fallida.pregunta.capitulo.tema

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# --- Modelos para el Temario ---

class Tema(models.Model):
    """
    Representa un bloque o tema principal de la oposición.
    Ej: "Bloque I: Derecho Constitucional"
    """
    titulo = models.CharField(
        _("título del tema"),
        max_length=255,
        unique=True,
        help_text=_("Título único para el tema principal.")
    )
    orden = models.PositiveIntegerField(
        _("orden"),
        default=0,
        db_index=True,
        help_text=_("Número para ordenar la lista de temas.")
    )

    class Meta:
        verbose_name = _("tema")
        verbose_name_plural = _("temas")
        ordering = ['orden', 'titulo']

    def __str__(self):
        return self.titulo


class Capitulo(models.Model):
    """
    Representa un capítulo, sección o epígrafe dentro de un Tema.
    Las preguntas se vincularán a este nivel.
    Ej: "Tema 1: La Constitución Española de 1978"
    """
    tema = models.ForeignKey(
        Tema,
        on_delete=models.CASCADE,
        related_name='capitulos',
        verbose_name=_("tema"),
        help_text=_("Tema principal al que pertenece este capítulo.")
    )
    titulo = models.CharField(
        _("título del capítulo"),
        max_length=255,
        help_text=_("Título del capítulo o epígrafe.")
    )
    contenido = models.TextField(
        _("contenido del capítulo"),
        blank=True,
        help_text=_("Descripción o contenido. Puedes usar Markdown o reStructuredText.")
    )
    orden = models.PositiveIntegerField(
        _("orden"),
        default=0,
        help_text=_("Número para ordenar los capítulos dentro de un mismo tema.")
    )

    class Meta:
        verbose_name = _("capítulo")
        verbose_name_plural = _("capítulos")
        unique_together = ('tema', 'titulo')
        ordering = ['tema', 'orden', 'titulo']

    def __str__(self):
        return f"{self.tema.titulo}: {self.titulo}"


# --- Modelo para las Preguntas (VERSIÓN COMPLETA Y CORREGIDA) ---

class Pregunta(models.Model):
    """
    Representa una pregunta de tipo test.
    Cada pregunta está asociada a un Capítulo específico.
    """
    class OpcionesRespuesta(models.TextChoices):
        A = 'A', 'Respuesta A'
        B = 'B', 'Respuesta B'
        C = 'C', 'Respuesta C'
        D = 'D', 'Respuesta D'

    capitulo = models.ForeignKey(
        Capitulo,
        on_delete=models.CASCADE,
        related_name='preguntas',
        verbose_name=_("capítulo"),
        help_text=_("El capítulo al que pertenece esta pregunta.")
    )
    enunciado = models.TextField(
        _("enunciado de la pregunta"),
        help_text=_("El texto de la pregunta. También puede usar Markdown.")
    )
    respuesta_a = models.TextField(_("respuesta A"))
    respuesta_b = models.TextField(_("respuesta B"))
    respuesta_c = models.TextField(_("respuesta C"))
    respuesta_d = models.TextField(_("respuesta D"))

    respuesta_correcta = models.CharField(
        _("respuesta correcta"),
        max_length=1,
        choices=OpcionesRespuesta.choices,
        help_text=_("Marca la letra de la respuesta correcta.")
    )
    explicacion = models.TextField(
        _("explicación"),
        blank=True,
        null=True,
        help_text=_("Explicación opcional sobre por qué la respuesta es correcta. Admite Markdown.")
    )
    activa = models.BooleanField(
        _("activa"),
        default=True,
        help_text=_("Desmarca para ocultar esta pregunta en los nuevos exámenes.")
    )

    class Meta:
        verbose_name = _("pregunta")
        verbose_name_plural = _("preguntas")
        ordering = ['capitulo']

    def __str__(self):
        return f"Pregunta de '{self.capitulo.titulo}': {self.enunciado[:50]}..."


# --- Modelos para Exámenes y Resultados ---

class Examen(models.Model):
    """
    Representa un examen o simulación realizado por un usuario.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='examenes',
        verbose_name=_("usuario")
    )
    preguntas = models.ManyToManyField(
        Pregunta,
        related_name='examenes',
        verbose_name=_("preguntas")
    )
    fecha_creacion = models.DateTimeField(
        _("fecha de creación"),
        auto_now_add=True
    )
    fecha_finalizacion = models.DateTimeField(
        _("fecha de finalización"),
        null=True,
        blank=True
    )
    puntuacion = models.FloatField(
        _("puntuación"),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("examen")
        verbose_name_plural = _("exámenes")
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Examen de {self.usuario.username} - {self.fecha_creacion.strftime('%d/%m/%Y %H:%M')}"


class RespuestaUsuario(models.Model):
    """
    Almacena la respuesta de un usuario a una pregunta en un examen.
    """
    examen = models.ForeignKey(
        Examen,
        on_delete=models.CASCADE,
        related_name='respuestas_usuario',
        verbose_name=_("examen")
    )
    pregunta = models.ForeignKey(
        Pregunta,
        on_delete=models.CASCADE,
        related_name='respuestas_usuario',
        verbose_name=_("pregunta")
    )
    respuesta_seleccionada = models.CharField(
        _("respuesta seleccionada"),
        max_length=1,
        choices=Pregunta.OpcionesRespuesta.choices
    )
    es_correcta = models.BooleanField(
        _("es correcta"),
        default=False
    )

    class Meta:
        verbose_name = _("respuesta de usuario")
        verbose_name_plural = _("respuestas de usuario")
        unique_together = ('examen', 'pregunta')

    def save(self, *args, **kwargs):
        self.es_correcta = self.respuesta_seleccionada == self.pregunta.respuesta_correcta
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Respuesta a '{self.pregunta.enunciado[:30]}...' en examen {self.examen.id}"