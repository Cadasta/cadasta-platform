import os
from .default import *  # NOQA

DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'cadasta',
        'USER': 'cadasta',
        'PASSWORD': 'cadasta',
        'HOST': 'localhost',
    }
}

DJOSER.update({  # NOQA
    'DOMAIN': 'localhost:8000',
})
ALLOWED_HOSTS = ['*']
# devserver settings
DEVSERVER_AUTO_PROFILE = False  # use decorated functions
DEVSERVER_TRUNCATE_SQL = True  # squash verbose output, show from/where
DEVSERVER_MODULES = (
    # uncomment if you want to show every SQL executed
    # 'devserver.modules.sql.SQLRealTimeModule',
    # show sql query summary
    'devserver.modules.sql.SQLSummaryModule',
    # Total time to render a request
    'devserver.modules.profile.ProfileSummaryModule',

    # Modules not enabled by default
    # 'devserver.modules.ajax.AjaxDumpModule',
    # 'devserver.modules.profile.MemoryUseModule',
    # 'devserver.modules.cache.CacheSummaryModule',
    # see documentation for line profile decorator examples
    # 'devserver.modules.profile.LineProfilerModule',
    # show django session information
    # 'devserver.modules.request.SessionInfoModule',
)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = 'testing@example.com'

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
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'default'
    },
    'jsonattrs': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'jsonattrs'
    }
}

# Debug logging...
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/debug.log',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'xform.submissions': {
            'handlers': ['file'],
            'level': 'DEBUG'
        }
    },
}

ES_PORT = '8000'

# Async Tooling
CELERY_BROKER_TRANSPORT = 'sqs' if os.environ.get('SQS') else 'memory'
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'region': 'us-west-2',
    'queue_name_prefix': '{}-'.format(os.environ.get('QUEUE-PREFIX', 'dev')),
    'wait_time_seconds': 20,
    'visibility_timeout': 20,
} if CELERY_BROKER_TRANSPORT.lower() == 'sqs' else {}
