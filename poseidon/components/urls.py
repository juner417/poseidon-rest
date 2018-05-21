from django.conf.urls import url
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from components import views

urlpatterns = [
    url(r'^components$', views.ComponentController.as_view()),
    url(r'^components/(?P<uuid>[a-zA-Z]+\-[a-zA-Z0-9]+)$', views.ComponentController.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
