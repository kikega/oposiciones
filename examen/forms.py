"""Formularios para el panel de carga de datos del staff."""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Oposicion, Tema, Capitulo, Articulo, Pregunta


class TemaModelChoiceField(forms.ModelChoiceField):
    """Sobrescribe la renderización del dropdown para incluir el número de orden visiblemente."""
    def label_from_instance(self, obj):
        titulo_truncado = (obj.titulo[:90] + "...") if len(obj.titulo) > 90 else obj.titulo
        # Ejemplo: "Tema 1: La Constitución Española..."
        return f"Tema {obj.orden}: {titulo_truncado}"


class PreguntaStaffForm(forms.ModelForm):
    """Formulario guiado para la creación de preguntas por el staff.

    Incorpora campos de navegación (oposicion_selector, tema_selector,
    capitulo_selector) que NO se persisten en base de datos; se usan para
    filtrar en cascada el campo `articulo` vía AJAX desde el frontend.
    """

    # --- Campos de navegación en cascada (no son campos del modelo) ---
    tema_selector = TemaModelChoiceField(
        queryset=Tema.objects.all().order_by('orden', 'titulo'),
        label=_('1. Selecciona el Tema'),
        required=True,
        empty_label=_('-- Elige un tema --'),
        widget=forms.Select(attrs={
            'id': 'id_tema_selector',
            'class': 'form-select form-select-lg',
        }),
        help_text=_('Filtra los capítulos disponibles según el tema.'),
    )
    capitulo_selector = forms.ModelChoiceField(
        queryset=Capitulo.objects.none(),
        label=_('3. Selecciona el Capítulo'),
        required=True,
        empty_label=_('-- Primero elige un tema --'),
        widget=forms.Select(attrs={
            'id': 'id_capitulo_selector',
            'class': 'form-select form-select-lg',
            'disabled': 'disabled',
        }),
        help_text=_('Filtra los artículos disponibles según el capítulo.'),
    )

    class Meta:
        model = Pregunta
        fields = [
            # Campos de navegación (no del modelo)
            'tema_selector',
            'capitulo_selector',
            # Campos reales del modelo
            'articulo',
            'enunciado',
            'respuesta_a',
            'respuesta_b',
            'respuesta_c',
            'respuesta_d',
            'respuesta_correcta',
            'explicacion',
        ]
        widgets = {
            'articulo': forms.Select(attrs={
                'id': 'id_articulo',
                'class': 'form-select form-select-lg',
                'disabled': 'disabled',
            }),
            'enunciado': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Escribe el enunciado de la pregunta...'),
            }),
            'respuesta_a': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Respuesta A...'),
            }),
            'respuesta_b': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Respuesta B...'),
            }),
            'respuesta_c': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Respuesta C...'),
            }),
            'respuesta_d': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Respuesta D...'),
            }),
            'respuesta_correcta': forms.RadioSelect(attrs={
                'class': 'form-check-input',
            }),
            'explicacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Explicación opcional para la respuesta correcta...'),
            }),
        }
        labels = {
            'articulo': _('3. Artículo de Referencia'),
            'enunciado': _('Enunciado de la pregunta'),
            'respuesta_a': _('Respuesta A'),
            'respuesta_b': _('Respuesta B'),
            'respuesta_c': _('Respuesta C'),
            'respuesta_d': _('Respuesta D'),
            'respuesta_correcta': _('Respuesta correcta'),
            'explicacion': _('Explicación (opcional)'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restringir el queryset de artículo al inicio
        self.fields['articulo'].queryset = Articulo.objects.none()
        self.fields['articulo'].empty_label = _('-- Primero elige un capítulo --')

        # Si el formulario vuelve con datos (POST), reconstruir los querysets
        # para que la validación no falle por opciones inválidas.

        if 'tema_selector' in self.data:
            try:
                tema_id = int(self.data.get('tema_selector'))
                self.fields['capitulo_selector'].queryset = Capitulo.objects.filter(
                    tema__id=tema_id
                ).order_by('orden', 'titulo')
                self.fields['capitulo_selector'].widget.attrs.pop('disabled', None)
            except (ValueError, TypeError):
                pass

        if 'capitulo_selector' in self.data:
            try:
                capitulo_id = int(self.data.get('capitulo_selector'))
                self.fields['articulo'].queryset = Articulo.objects.filter(
                    capitulo__id=capitulo_id
                ).order_by('numero')
                self.fields['articulo'].widget.attrs.pop('disabled', None)
            except (ValueError, TypeError):
                pass
