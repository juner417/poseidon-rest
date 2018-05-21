from django.conf.urls import include, url
from django.contrib import admin
from poseidon import views
from rest_framework_swagger.views import get_swagger_view
#from rest_framework.documentation import include_docs_urls

urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^swagger-ui$', get_swagger_view(title='Poseidon API')),
    url(r'^poseidon/v1/api/', include('clusters.urls', namespace="clusters")),
    url(r'^poseidon/v1/api/', include('nodes.urls', namespace="nodes")),
    url(r'^poseidon/v1/api/', include('components.urls', namespace="components")),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    #url(r'^docs/', include_docs_urls(title='Poseidon API doc')),
    url(r'^admin/', admin.site.urls),
]
