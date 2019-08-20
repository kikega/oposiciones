from django.db import models
from django.contrib.postgres.fields import ArrayField

# Create your models here.
class Examen(models.Model):
    fecha = models.DateField(auto_now=True)
    p_falladas = ArrayField(models.IntegerField())
    p_acertadas = models.IntegerField()
    fallos = models.IntegerField()
    nota = models.FloatField()

    class Meta:
    	verbose_name_plural = "Examenes"
	
    def __str__(self):
    	return str(self.fecha)
