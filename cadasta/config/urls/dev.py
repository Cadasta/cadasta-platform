from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    url(r'', include('config.urls.default')),
    url(r'', include('buckets.test.urls')),
    url(r'', include('search.mock_es.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

try:
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]
except ImportError:
    pass
