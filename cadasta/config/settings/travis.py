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

DEFAULT_FILE_STORAGE = 'buckets.test.storage.FakeS3Storage'
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'core/media')
MEDIA_URL = '/media/'
