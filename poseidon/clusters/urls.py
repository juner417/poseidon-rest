from django.conf.urls import url
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from clusters import views
from nodes import views as node_views
from components import views as compo_views

urlpatterns = [
    url(r'^clusters$', views.ClusterController.as_view()),
    url(r'^clusters/(?P<uuid>[a-zA-Z]+\-[a-zA-Z0-9]+)$', views.ClusterController.as_view()),
    url(r'^clusters/(?P<cluster_uuid>[a-zA-Z]+\-[a-zA-Z0-9]+)/nodes$', node_views.NodeJoinViewer.as_view()),
    url(r'^clusters/(?P<cluster_uuid>[a-zA-Z]+\-[a-zA-Z0-9]+)/nodes/(?P<node_uuid>[a-zA-Z]+\-[a-zA-Z0-9]+)$', node_views.NodeJoinViewer.as_view()),
    url(r'^clusters/(?P<uuid>[a-zA-Z]+\-[a-zA-Z0-9]+)/components$', compo_views.ComponentJoinViewer.as_view()),
    url(r'^clusters/(?P<uuid>[a-zA-Z]+\-[a-zA-Z0-9]+)/components/(?P<compo_uuid>[a-zA-Z]+\-[a-zA-Z0-9]+)$', compo_views.ComponentJoinViewer.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
