from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# Create your views here.
class HomeView(LoginRequiredMixin, TemplateView):
    """Home de la aplicación"""
    template_name = 'examen/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

