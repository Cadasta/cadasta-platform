from .default import *

DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'cadasta',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '',
    }
}

DJOSER.update({
    'SEND_ACTIVATION_EMAIL': False,
})
