from datetime import datetime

import pytz

from django.conf import settings

# 10,000,000 bytes
DEFAULT_CONTENT_LENGTH = getattr(settings, 'DEFAULT_CONTENT_LENGTH', 10000000)


class OpenRosaHeadersMixin(object):

    DEFAULT_CONTENT_TYPE = 'application/xml'

    def get_openrosa_headers(
            self, request, location=True, content_length=True):

        tz = pytz.timezone(settings.TIME_ZONE)
        dt = datetime.now(tz).strftime('%a, %d %b %Y %H:%M:%S %Z')

        data = {
            'Date': dt,
            'X-OpenRosa-Version': '1.0'
        }

        if content_length:
            data['X-OpenRosa-Accept-Content-Length'] = DEFAULT_CONTENT_LENGTH

        if location:
            data['Location'] = request.build_absolute_uri(request.path)

        return data
