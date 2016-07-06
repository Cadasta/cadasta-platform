from django.conf.urls import include, url


urlpatterns = [
    url(r'', include('config.urls.default')),
    url(r'', include('buckets.urls')),
]
