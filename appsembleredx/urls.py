from django.conf import settings
from django.conf.urls import include, patterns, url

urlpatterns = patterns(
    'boilerplate.views',
    url(r'^$','index', name='index'),
)
