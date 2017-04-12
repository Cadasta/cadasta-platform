from .default import *  # NOQA

DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'cadasta',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '',
    }
}

DJOSER.update({  # NOQA
    'SEND_ACTIVATION_EMAIL': False,
})

ROOT_URLCONF = 'config.urls.dev'
DEFAULT_FILE_STORAGE = 'buckets.test.storage.FakeS3Storage'

# Use HTTP for OSM for testing only, to make caching tiles for
# functional tests a bit simpler.
LEAFLET_CONFIG['TILES'][0] = (
    LEAFLET_CONFIG['TILES'][0][0],
    'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    LEAFLET_CONFIG['TILES'][0][2]
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    },
    'jsonattrs': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'jsonattrs'
    }
}

# Async Tooling
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_BROKER_TRANSPORT = 'memory'
