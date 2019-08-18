from django.db import models
from tinymce import HTMLField

# Create your models here.

class Oposicion(models.Model):
    oposicion = models.CharField(, max_length=200)

    class Meta:
        verbose_name = "Oposición"
        verbose_name_plural = "Oposiciones"

    def __str__(self):
        return self.oposicion
    

class Tema(models.Model):
    tema = models.IntegerField()
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    oposicion = models.ForeignKey(Oposicion)

    class Meta:
        ordering = ['tema']
        verbose_name_plural = "Temas"

    def __str__(self):
        return '%s, %s' % (self.tema, self.descripcion)


class Capitulo(models.Model):
    capitulo = models.CharField(max_length=10)
    titulo = models.CharField(max_length=200)
    contenido = HTMLField('Contenido')
    tema = models.ForeignKey(Tema)

    class Meta:
        ordering = ['capitulo']
        verbose_name = "Capitulo"
        verbose_name_plural = "Capitulos"

    def __str__(self):
        return '%s %s' % (self.capitulo, self.titulo)

    
class Pregunta(models.Model):
    pregunta = models.TextField(max_length=255)
    res_a = models.TextField(max_length=255)
    res_b = models.TextField(max_length=255)
    res_c = models.TextField(max_length=255)
    correcta = models.CharField(max_length = 1)
    tema = models.ForeignKey(Tema, blank=True, null=True)
    capitulo = models.ForeignKey(Capitulo, blank=True, null=True)

    def __str__(self):
        return '%s %s %s %s' % (self.pregunta, self.res_a, self.res_b, self.res_c)