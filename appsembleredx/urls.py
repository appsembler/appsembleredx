from django.conf.urls import patterns, url

urlpatterns = patterns(
    'boilerplate.views',
    url(r'^$', 'index', name='index'),
)
