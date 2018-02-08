import os
import requests
from .default import *  # NOQA

INSTALLED_APPS += (  # NOQA
    'opbeat.contrib.django',
)

MIDDLEWARE_CLASSES = (
    'opbeat.contrib.django.middleware.OpbeatAPMMiddleware',
    'opbeat.contrib.django.middleware.Opbeat404CatchMiddleware',
) + MIDDLEWARE_CLASSES  # NOQA

DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']

DEFAULT_FILE_STORAGE = 'buckets.storage.S3Storage'

AWS = {
    'BUCKET': os.environ['S3_BUCKET'],
    'ACCESS_KEY': os.environ['S3_ACCESS_KEY'],
    'SECRET_KEY': os.environ['S3_SECRET_KEY'],
    'REGION': 'us-west-2',
    'MAX_FILE_SIZE': 10485760,
}

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'cadasta',
        'USER': 'cadasta',
        'PASSWORD': os.environ['DB_PASS'],
        'HOST': os.environ['DB_HOST']
    }
}

CACHES = {
    'default': {
        'BACKEND': 'core.backends.MemorySafePyLibMCCache',
        'LOCATION': [
            os.environ['MEMCACHED_HOST'],
        ],
        'OPTIONS': {'distribution': 'consistent'}
    },
    'jsonattrs': {
        'BACKEND': 'core.backends.MemorySafePyLibMCCache',
        'LOCATION': [
            os.environ['MEMCACHED_HOST'],
        ],
        'OPTIONS': {'distribution': 'consistent'}
    }
}

ES_HOST = os.environ['ES_HOST']

OPBEAT = {
    'ORGANIZATION_ID': os.environ['OPBEAT_ORGANIZATION_ID'],
    'APP_ID': os.environ['OPBEAT_APP_ID'],
    'SECRET_TOKEN': os.environ['OPBEAT_SECRET_TOKEN'],
    'ASYNC': True,
}

DJOSER.update({  # NOQA
    'DOMAIN': os.environ['DOMAIN'],
})

SESSION_COOKIE_AGE = 7200
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Adding localhost here for uWSGI debugging!
ALLOWED_HOSTS = [os.environ['API_HOST'], os.environ['DOMAIN'], 'localhost']
try:
    # Append local ip to ALLOWED_HOSTS to allow successful responses from
    # AWS ELB healthcheck
    local_ip_url = 'http://169.254.169.254/latest/meta-data/local-ipv4'
    ALLOWED_HOSTS.append(requests.get(local_ip_url, timeout=0.01).text)
except requests.exceptions.RequestException:
    pass

ADMINS = [('Cadasta platform admins', 'platform-admin@cadasta.org'),
          ('Cadasta Platform Errors', os.environ['SLACK_HOOK'])]
EMAIL_HOST = 'email-smtp.us-west-2.amazonaws.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
SERVER_EMAIL = 'platform@cadasta.org'
DEFAULT_FROM_EMAIL = 'Cadasta Platform <platform@cadasta.org>'
ROOT_URLCONF = 'config.urls.production'

STATIC_URL = '/static/'
STATIC_ROOT = '/opt/cadasta/static'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/opt/cadasta/media'

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
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/debug.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'simple'
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/error.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'simple'
        },
        'requests_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/requests.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'simple'
        },
        'email_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'opbeat': {
            'level': 'WARNING',
            'class': 'opbeat.contrib.django.handlers.OpbeatHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'core': {
            'handlers': ['file', 'error_file', 'email_admins', 'opbeat'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'xform.submissions': {
            'handlers': ['file', 'error_file', 'email_admins', 'opbeat'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # Log errors from the Opbeat module to the console
        'opbeat.errors': {
            'level': 'ERROR',
            'handlers': ['file', 'error_file'],
            'propagate': False,
        },
    },
}

SMS_GATEWAY = 'accounts.gateways.TwilioGateway'
TWILIO_PHONE = os.environ['TWILIO_PHONE']

# Async Tooling
CELERY_BROKER_TRANSPORT = 'sqs'
CELERY_QUEUE_PREFIX = os.environ['QUEUE_PREFIX']
