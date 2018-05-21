from django.views.generic.base import TemplateView
from rest_framework import renderers
from rest_framework.decorators import permission_classes, api_view, renderer_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.schemas import SchemaGenerator
from rest_framework.views import APIView
from rest_framework_swagger import renderers

class HomeView(TemplateView):

    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['object_list'] = ['clusters', 'nodes', 'components']
        return context
