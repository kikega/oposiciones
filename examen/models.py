from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver


# --- Modelos para el Temario ---

class Oposicion(models.Model):
    """Representa una oposición específica. Ej: 'Auxiliar Administrativo del Estado'."""

    nombre = models.CharField(
        _("nombre de la oposición"), max_length=255, unique=True,
        help_text=_("Nombre único para la oposición.")
    )
    descripcion = models.TextField(
        _("descripción"), blank=True, null=True,
        help_text=_("Descripción opcional de la oposición.")
    )
    num_preguntas = models.PositiveIntegerField(
        _("número de preguntas por test"), default=100,
        help_text=_("Nº de preguntas aleatorias que se generan en cada simulacro.")
    )
    penalizacion = models.DecimalField(
        _("penalización por error"), max_digits=4, decimal_places=2, default='0.33',
        help_text=_("Fracción de punto que se resta por cada respuesta errónea.")
    )

    class Meta:
        verbose_name = _("oposición")
        verbose_name_plural = _("oposiciones")
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class PerfilUsuario(models.Model):
    """Perfil extendido del usuario: datos personales y oposiciones."""
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    oposiciones_inscritas = models.ManyToManyField(Oposicion, related_name='alumnos', blank=True)
    oposicion_activa = models.ForeignKey(Oposicion, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios_activos')

    # Datos personales
    nombre = models.CharField(_("nombre"), max_length=100, blank=True, default='')
    apellidos = models.CharField(_("apellidos"), max_length=150, blank=True, default='')
    telefono = models.CharField(_("teléfono"), max_length=20, blank=True, default='')
    fecha_nacimiento = models.DateField(_("fecha de nacimiento"), null=True, blank=True)
    ciudad = models.CharField(_("ciudad"), max_length=100, blank=True, default='')
    bio = models.TextField(_("notas personales / motivación"), blank=True, default='',
                           help_text=_("Espacio libre para tus apuntes de motivación o plan de estudio."))

    def __str__(self):
        nombre_completo = f"{self.nombre} {self.apellidos}".strip()
        return nombre_completo or self.usuario.email

    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo o el email si no hay datos."""
        return f"{self.nombre} {self.apellidos}".strip() or self.usuario.email

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def guardar_perfil_usuario(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()


class Tema(models.Model):
    """Tema de estudio transversal que puede pertenecer a múltiples oposiciones. Ej: 'Tema 1: La Constitución Española de 1978'."""

    oposiciones = models.ManyToManyField(
        Oposicion, related_name='temas',
        verbose_name=_("oposiciones"), help_text=_("Oposiciones a las que pertenece este tema.")
    )
    bloque = models.CharField(
        _("bloque"), max_length=150, blank=True, null=True,
        help_text=_("Nombre o identificador del bloque. Ej: 'Bloque I' o 'Informática'.")
    )
    orden = models.PositiveIntegerField(
        _("orden"), default=0,
        help_text=_("Número para ordenar los temas (referencial, ya que puede variar por oposición).")
    )
    titulo = models.TextField(
        _("título del tema"),
        help_text=_("Título del tema o epígrafe.")
    )
    documentacion = models.FileField(
        _("documentación"), upload_to="pdf/temas/", max_length=255,
        blank=True, null=True, help_text=_("Archivo PDF del Tema.")
    )

    class Meta:
        verbose_name = _("tema")
        verbose_name_plural = _("temas")
        ordering = ['orden', 'titulo']

    def __str__(self):
        return self.titulo


class Capitulo(models.Model):
    """Capítulo dentro de un tema."""

    tema = models.ForeignKey(
        Tema, on_delete=models.CASCADE, related_name='capitulosTema',
        verbose_name=_("tema"), help_text=_("Tema al que pertenece este capítulo.")
    )
    orden = models.PositiveIntegerField(
        _("orden"), default=0,
        help_text=_("Número para ordenar los capítulos dentro de un mismo tema.")
    )
    titulo = models.CharField(
        _("título del capítulo"), max_length=255,
        help_text=_("Título del capítulo o epígrafe.")
    )
    importancia = models.PositiveIntegerField(
        _("importancia o frecuencia"), default=1,
        help_text=_("Nivel de importancia del capítulo (ej. 1=Normal, 2=Importante, 3=Muy Importante).")
    )
    fecha_actualizacion_ley = models.DateField(
        _("fecha de actualización legislativa"), blank=True, null=True,
        help_text=_("Fecha en que este capítulo fue modificado por cambios legislativos.")
    )
    es_modificacion_reciente = models.BooleanField(
        _("modificación reciente"), default=False,
        help_text=_("Indica si este capítulo ha sufrido modificaciones legislativas recientes.")
    )


    class Meta:
        verbose_name = _("capítulo")
        verbose_name_plural = _("capítulos")
        unique_together = ('tema', 'titulo')
        ordering = ['tema', 'orden', 'titulo']

    def __str__(self):
        return f"{self.tema.titulo}: {self.titulo}"


class Articulo(models.Model):
    """Artículo dentro de un capítulo. Admite Markdown en contenido."""

    capitulo = models.ForeignKey(
        Capitulo, on_delete=models.CASCADE, related_name='articulosCapitulo',
        verbose_name=_('capítulo'), help_text=_("Capítulo al que pertenece este artículo.")
    )

    contenido = models.TextField(
        _("contenido del artículo"),
        help_text=_("Contenido completo del artículo. Admite Markdown.")
    )
    numero = models.CharField(
        _("número del artículo"), max_length=50,
        help_text=_("Número o identificador del artículo dentro del capítulo.")
    )

    class Meta:
        verbose_name = _("artículo")
        verbose_name_plural = _("artículos")
        unique_together = [('capitulo', 'numero')]
        ordering = ['capitulo', 'numero']

    def __str__(self):
        return f"Art. {self.numero} - {self.capitulo.titulo}"


# --- Modelos de Recursos y Progreso ---

class RecursoTema(models.Model):
    """Recursos multimedia adicionales para un capítulo."""
    class TipoRecurso(models.TextChoices):
        VIDEO = 'VIDEO', _('Vídeo')
        AUDIO = 'AUDIO', _('Audio/Podcast')
        ESQUEMA = 'ESQUEMA', _('Esquema/Mapa Mental')
        DOCUMENTO = 'DOCUMENTO', _('Documento Anexo')

    capitulo = models.ForeignKey(
        Capitulo, on_delete=models.CASCADE, related_name='recursos',
        verbose_name=_("capítulo")
    )
    titulo = models.CharField(_("título del recurso"), max_length=255)
    tipo = models.CharField(
        _("tipo de recurso"), max_length=20, choices=TipoRecurso.choices, default=TipoRecurso.DOCUMENTO
    )
    url = models.URLField(
        _("URL del recurso"), max_length=500, blank=True, null=True,
        help_text=_("Enlace al recurso (ej. YouTube, Spotify o Drive).")
    )
    archivo = models.FileField(
        _("archivo"), upload_to="recursos_capitulos/", max_length=255,
        blank=True, null=True, help_text=_("Archivo local si no se usa URL.")
    )

    class Meta:
        verbose_name = _("recurso de tema")
        verbose_name_plural = _("recursos de tema")
        ordering = ['capitulo', 'tipo', 'titulo']

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo} - {self.capitulo}"

class ProgresoEstudio(models.Model):
    """Registro del progreso de estudio de un usuario por capítulo."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='progresos_estudio', verbose_name=_("usuario")
    )
    capitulo = models.ForeignKey(
        Capitulo, on_delete=models.CASCADE, related_name='progresos_usuarios',
        verbose_name=_("capítulo")
    )
    completado = models.BooleanField(_("completado"), default=False)
    fecha_completado = models.DateTimeField(_("fecha de finalización"), null=True, blank=True)

    class Meta:
        verbose_name = _("progreso de estudio")
        verbose_name_plural = _("progresos de estudio")
        unique_together = ('usuario', 'capitulo')

    def __str__(self):
        estado = "Completado" if self.completado else "Pendiente"
        return f"{self.usuario.email} - {self.capitulo.titulo}: {estado}"

# --- Modelo para Notas de Estudio ---

class NotaEstudio(models.Model):
    """Notas privadas de un usuario para un capítulo específico."""
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notas_estudio', verbose_name=_("usuario")
    )
    capitulo = models.ForeignKey(
        Capitulo, on_delete=models.CASCADE, related_name='notas',
        verbose_name=_("capítulo")
    )
    contenido = models.TextField(
        _("contenido"), blank=True,
        help_text=_("Tus apuntes personales sobre este capítulo.")
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("nota de estudio")
        verbose_name_plural = _("notas de estudio")
        unique_together = ('usuario', 'capitulo')
        ordering = ['-fecha_actualizacion']

    def __str__(self):
        return f"Notas de {self.usuario.email} - {self.capitulo}"


# --- Modelo para las Preguntas ---

class Pregunta(models.Model):
    """Pregunta de tipo test con 4 opciones de respuesta."""

    class OpcionesRespuesta(models.TextChoices):
        A = 'A', 'Respuesta A'
        B = 'B', 'Respuesta B'
        C = 'C', 'Respuesta C'
        D = 'D', 'Respuesta D'

    enunciado = models.TextField(
        _("enunciado"), help_text=_("El texto de la pregunta. Admite Markdown.")
    )
    respuesta_a = models.TextField(_("respuesta A"))
    respuesta_b = models.TextField(_("respuesta B"))
    respuesta_c = models.TextField(_("respuesta C"))
    respuesta_d = models.TextField(_("respuesta D"))
    respuesta_correcta = models.CharField(
        _("respuesta correcta"), max_length=1,
        choices=OpcionesRespuesta.choices,
        help_text=_("Letra de la respuesta correcta.")
    )
    explicacion = models.TextField(
        _("explicación"), blank=True, null=True,
        help_text=_("Explicación opcional. Admite Markdown.")
    )
    articulo = models.ForeignKey(
        Articulo, on_delete=models.CASCADE, related_name='preguntasArticulo',
        verbose_name=_("artículo"), help_text=_("Artículo al que pertenece esta pregunta.")
    )

    class Meta:
        verbose_name = _("pregunta")
        verbose_name_plural = _("preguntas")
        ordering = ['articulo']

    def __str__(self):
        return f"{self.enunciado[:60]}..."

    def get_absolute_url(self):
        return reverse('pregunta-detalle', kwargs={'pk': self.pk})

    def get_respuesta_texto(self, letra: str) -> str:
        """Retorna el texto de la respuesta para la letra dada ('A','B','C','D')."""
        mapping = {
            'A': self.respuesta_a,
            'B': self.respuesta_b,
            'C': self.respuesta_c,
            'D': self.respuesta_d,
        }
        return mapping.get(letra.upper(), '')

    @property
    def todas_respuestas(self) -> dict:
        """Retorna un dict con todas las respuestas."""
        return {
            'A': self.respuesta_a,
            'B': self.respuesta_b,
            'C': self.respuesta_c,
            'D': self.respuesta_d,
        }

    @property
    def texto_respuesta_correcta(self) -> str:
        """Retorna el texto de la respuesta correcta."""
        return self.get_respuesta_texto(self.respuesta_correcta)


# --- Modelos para Exámenes y Resultados ---

class Examen(models.Model):
    """Representa un examen o simulación realizado por un usuario."""

    class TipoExamen(models.TextChoices):
        SIMULACRO = 'SIMULACRO', _('Simulacro general')
        REPASO = 'REPASO', _('Repaso de errores')
        TEMA = 'TEMA', _('Por tema específico')
        CAPITULO = 'CAPITULO', _('Por capítulo específico')

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='examenes', verbose_name=_("usuario")
    )
    oposicion = models.ForeignKey(
        Oposicion, on_delete=models.SET_NULL, related_name='examenes',
        verbose_name=_("oposición"), null=True, blank=True,
        help_text=_("Oposición a la que pertenece este examen.")
    )
    tipo = models.CharField(
        _("tipo"), max_length=10, choices=TipoExamen.choices,
        default=TipoExamen.SIMULACRO,
    )
    fecha_creacion = models.DateTimeField(_("fecha de creación"), auto_now_add=True)
    fecha_finalizacion = models.DateTimeField(
        _("fecha de finalización"), null=True, blank=True
    )
    preguntas = models.ManyToManyField(
        Pregunta, related_name='examenes', verbose_name=_("preguntas")
    )
    respuestas_correctas = models.PositiveIntegerField(
        default=0, verbose_name=_("Respuestas correctas"),
    )
    respuestas_erroneas = models.PositiveIntegerField(
        default=0, verbose_name=_("Respuestas erróneas"),
    )
    puntuacion = models.FloatField(
        _("puntuación"), null=True, blank=True,
        help_text=_("Puntuación total obtenida en el examen.")
    )

    class Meta:
        verbose_name = _("examen")
        verbose_name_plural = _("exámenes")
        ordering = ['-fecha_creacion']

    def __str__(self):
        return (
            f"{self.get_tipo_display()} #{self.pk} — "
            f"{self.usuario.email} [{self.fecha_creacion.strftime('%d/%m/%Y')}]"
        )

    def get_absolute_url(self):
        return reverse('examen:simulacion_resultados', kwargs={'examen_id': self.pk})

    @property
    def porcentaje_acierto(self) -> float:
        """Calcula el porcentaje de acierto del examen sobre el total de preguntas."""
        total = self.preguntas.count()
        if total == 0:
            return 0.0
        return round((self.respuestas_correctas / total) * 100, 2)

    @property
    def total_respondidas(self) -> int:
        """Número total de preguntas respondidas (correctas + erróneas)."""
        return self.respuestas_correctas + self.respuestas_erroneas


class RespuestaUsuario(models.Model):
    """Almacena la respuesta de un usuario a una pregunta en un examen."""

    examen = models.ForeignKey(
        Examen, on_delete=models.CASCADE, related_name='respuestas_usuario',
        verbose_name=_("examen"),
    )
    pregunta = models.ForeignKey(
        Pregunta, on_delete=models.CASCADE, related_name='respuestas_usuario',
        verbose_name=_("pregunta")
    )
    respuesta_seleccionada = models.CharField(
        _("respuesta seleccionada"), max_length=1,
        choices=Pregunta.OpcionesRespuesta.choices
    )
    es_correcta = models.BooleanField(_("es correcta"), default=False)

    class Meta:
        verbose_name = _("respuesta de usuario")
        verbose_name_plural = _("respuestas de usuario")
        unique_together = ('examen', 'pregunta')

    def save(self, *args, **kwargs):
        self.es_correcta = (self.respuesta_seleccionada == self.pregunta.respuesta_correcta)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Respuesta a '{self.pregunta.enunciado[:30]}...' — examen #{self.examen.pk}"

    @property
    def texto_respuesta_seleccionada(self) -> str:
        """Retorna el texto de la respuesta seleccionada."""
        if not self.respuesta_seleccionada:
            return "Sin responder"
        return self.pregunta.get_respuesta_texto(self.respuesta_seleccionada)