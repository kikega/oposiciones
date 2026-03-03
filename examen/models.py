# Los modelos Examen y RespuestaUsuario no necesitan cambios.
# Siguen refiriéndose a Pregunta, y a través de Pregunta podemos llegar
# al Capítulo y al Tema para las estadísticas.
# Por ejemplo: respuesta_fallida.pregunta.capitulo.tema

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


# --- Modelos para el Temario ---
class Oposicion(models.Model):
    """
    Representa una oposición específica.
    Ej: "Oposición de Auxiliar Administrativo"
    """
    nombre = models.CharField(
        _("nombre de la oposición"),
        max_length=255,
        unique=True,
        help_text=_("Nombre único para la oposición.")
    )
    descripcion = models.TextField(
        _("descripción"),
        blank=True,
        null=True,
        help_text=_("Descripción opcional de la oposición.")
    )

    class Meta:
        verbose_name = _("oposición")
        verbose_name_plural = _("oposiciones")
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
class Bloque(models.Model):
    """
    Representa un bloque o tema principal de la oposición.
    Ej: "Bloque I: Derecho Constitucional"
    """
    titulo = models.CharField(
        _("título del bloque"),
        max_length=255,
        unique=True,
        help_text=_("Oposición a la que pertenece este bloque.")
    )
    orden = models.PositiveIntegerField(
        _("orden"),
        default=0,
        db_index=True,
        help_text=_("Número para ordenar la lista de bloques.")
    )

    class Meta:
        verbose_name = _("bloque")
        verbose_name_plural = _("bloques")
        ordering = ['orden', 'titulo']

    def __str__(self):
        return self.titulo
class Tema(models.Model):
    """
    Representa un capítulo, sección o epígrafe dentro de un Tema.
    Las preguntas se vincularán a este nivel.
    Ej: "Tema 1: La Constitución Española de 1978"
    """
    bloque = models.ForeignKey(
        Bloque,
        on_delete=models.CASCADE,
        related_name='temasBloque',
        verbose_name=_("bloque"),
        help_text=_("Bloque al que pertenece este tema.")
    )
    orden = models.PositiveIntegerField(
        _("orden"),
        default=0,
        help_text=_("Número para ordenar los temas dentro de un mismo bloque.")
    )
    titulo = models.CharField(
        _("título del tema"),
        max_length=255,
        help_text=_("Título del tema o epígrafe.")
    )
    documentacion = models.FileField(
        _("documentcion"),
        upload_to = "pdf",
        max_length = 255,
        blank=True,
        null=True,
        help_text = "Archivo PDF con la documentación del Tema."
    )

    class Meta:
        verbose_name = _("tema")
        verbose_name_plural = _("temas")
        unique_together = ('bloque', 'titulo')
        ordering = ['bloque', 'orden', 'titulo']

    def __str__(self):
        return f"{self.bloque.titulo}: {self.titulo}"


class Capitulo(models.Model):
    """
    Representa un capítulo, sección o epígrafe dentro de un Tema.
    Las preguntas se vincularán a este nivel.
    Ej: "Tema 1: La Constitución Española de 1978"
    """
    tema = models.ForeignKey(
        Tema,
        on_delete=models.CASCADE,
        related_name='capitulosTema',
        verbose_name=_("capitulos"),
        help_text=_("Capítulo de un tema.")
    )
    orden = models.PositiveIntegerField(
        _("orden"),
        default=0,
        help_text=_("Número para ordenar los capítulos dentro de un mismo tema.")
    )
    titulo = models.CharField(
        _("título del capítulo"),
        max_length=255,
        help_text=_("Título del capítulo o epígrafe.")
    )

    oposicion = models.ManyToManyField(
        Oposicion,
        related_name='capítulosOposicion',
        verbose_name=_("oposición"),
        help_text=_("Oposición al que pertenece este capítulo."),
        blank=True
    )

    class Meta:
        verbose_name = _("capítulo")
        verbose_name_plural = _("capítulos")
        unique_together = ('tema', 'titulo')
        ordering = ['tema', 'orden', 'titulo']

    def __str__(self):
        return f"{self.tema.titulo}: {self.titulo}"

class Articulo(models.Model):
    """Representa un articulo dentro de un tema
    Ej: "Artículo 1: Derechos y deberes fundamentales"
    """
    capitulo = models.ForeignKey(
        Capitulo,
        on_delete=models.CASCADE,
        related_name='artículosCapitulo',
        verbose_name=_('capitulos'),
        help_text=_("Capítulo al que pertenece este artículo.")
    )
    titulo = models.CharField(
        _("título del artículo"),
        max_length=255,
        unique=True,
        help_text=_("Título único para el artículo.")
    )
    contenido = models.TextField(
        _("contenido del artículo"),
        help_text=_("Contenido completo del artículo. Admite Markdown.")
    )
    numero = models.CharField(
        _("número del artículo"),  
        max_length=50,
        unique=True,
        help_text=_("Número o identificador único del artículo.")
    )
    class Meta:
        verbose_name = _("artículo")
        verbose_name_plural = _("artículos")
        ordering = ['numero']

    def __str__(self):
        return self.titulo
    


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
    articulo = models.ForeignKey(
        Articulo,
        on_delete=models.CASCADE,
        related_name='preguntasArticulo',
        verbose_name=_("artículo"),
        help_text=_("Artículo al que pertenece esta pregunta")
    )

    class Meta:
        verbose_name = _("pregunta")
        verbose_name_plural = _("preguntas")
        ordering = ['articulo']

    def __str__(self):
        return f"{self.enunciado[:50]}..."

    def get_absolute_url(self):
        """Devuelve la URL absoluta que permite acceder a una instancia especifica de la pregunta."""
        return reverse('pregunta-detalle', kwargs={'pk': self.pk})

    def get_respuesta_texto(self, letra):
        """
        Retorna el texto de la respuesta correspondiente a la letra dada.

        Args:
            letra (str): Letra de la respuesta ('A', 'B', 'C', 'D')

        Returns:
            str: Texto de la respuesta o cadena vacía si la letra no es válida
        """
        respuestas = {
            'A': self.respuesta_a,
            'B': self.respuesta_b,
            'C': self.respuesta_c,
            'D': self.respuesta_d,
        }
        return respuestas.get(letra.upper(), '')

    @property
    def todas_respuestas(self):
        """Retorna un diccionario con todas las respuestas."""
        return {
            'A': self.respuesta_a,
            'B': self.respuesta_b,
            'C': self.respuesta_c,
            'D': self.respuesta_d,
        }
    
    @property
    def texto_respuesta_correcta(self):
        """Retorna el texto de la respuesta correcta."""
        return self.get_respuesta_texto(self.respuesta_correcta)


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
    fecha_creacion = models.DateTimeField(
        _("fecha de creación"),
        auto_now_add=True
    )
    fecha_finalizacion = models.DateTimeField(
        _("fecha de finalización"),
        null=True,
        blank=True
    )
    preguntas = models.ManyToManyField(
        Pregunta,
        related_name='examenes',
        verbose_name=_("preguntas")
    )
    respuestas_correctas = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Respuestas correctas"),
        help_text=_("Número de respuestas correctas")
    )
    respuestas_erroneas = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Respuestas erróneas"),
        help_text=_("Número de respuestas erróneas")
    )
    puntuacion = models.FloatField(
        _("puntuación"),
        null=True,
        blank=True,
        help_text=_("Puntuación total obtenida en el examen")
    )

    class Meta:
        verbose_name = _("examen")
        verbose_name_plural = _("exámenes")
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Examen de {self.usuario.username} - {self.fecha_creacion.strftime('%d/%m/%Y %H:%M')}"

    def get_absolute_url(self):
        return reverse('examen-detalle', kwargs={'uuid': self.uuid})

    @property
    def porcentaje_acierto(self):
        """Calcula el porcentaje de acierto del examen."""
        return round((self.respuestas_correctas / 100) * 100, 2)

class RespuestaUsuario(models.Model):
    """
    Almacena la respuesta de un usuario a una pregunta en un examen.
    """
    examen = models.ForeignKey(
        Examen,
        on_delete=models.CASCADE,
        related_name='respuestas_usuario',
        verbose_name=_("examen"),
        help_text=_("Examen al que pertenece esta respuesta")
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

    @property
    def texto_respuesta_seleccionada(self):
        """Retorna el texto de la respuesta seleccionada."""
        if not self.respuesta_seleccionada:
            return "Sin responder"
        return self.pregunta.get_respuesta_texto(self.respuesta_seleccionada)
    
    