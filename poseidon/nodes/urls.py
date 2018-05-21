from django.conf.urls import url
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from nodes import views
from components import views as compo_views

urlpatterns = [
    url(r'^nodes$', views.NodeViewer.as_view()),
    url(r'^nodes/(?P<uuid>[a-zA-Z]+\-[a-zA-Z0-9]+)$', views.NodeViewer.as_view()),
    url(r'^nodes/(?P<uuid>[a-zA-Z]+\-[a-zA-Z0-9]+)/status$', views.NodeController.as_view()),
    url(r'^nodes/(?P<uuid>[a-zA-Z]+\-[a-zA-Z0-9]+)/components$', compo_views.ComponentJoinViewer.as_view()),
    url(r'^nodes/(?P<uuid>[a-zA-Z]+\-[a-zA-Z0-9]+)/components/(?P<compo_uuid>[a-zA-Z]+\-[a-zA-Z0-9]+)$', compo_views.ComponentJoinViewer.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
