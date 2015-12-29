from .default import *

DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django_app',
        'USER': 'django',
        'PASSWORD': 'sdjgh34iutwefhfgbqkj3',
        'HOST': 'localhost',
    }
}

# devserver must be first thing in the list of insalled apps
INSTALLED_APPS = (
    # 'devserver',
) + INSTALLED_APPS

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
