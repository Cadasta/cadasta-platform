from collections import OrderedDict
import random
import string

import django.utils.text as base_utils
from django.conf import settings
from rest_framework.settings import api_settings
from rest_framework.utils.urls import replace_query_param, remove_query_param


ID_FIELD_LENGTH = 24

alphabet = string.ascii_lowercase + string.digits
for loser in 'l1o0':
    i = alphabet.index(loser)
    alphabet = alphabet[:i] + alphabet[i + 1:]


def byte_to_base32_chr(byte):
    return alphabet[byte & 31]


def random_id():
    rand_id = [random.randint(0, 0xFF) for i in range(ID_FIELD_LENGTH)]
    return ''.join(map(byte_to_base32_chr, rand_id))


def slugify(text, max_length=None, allow_unicode=False):
    slug = base_utils.slugify(text, allow_unicode=allow_unicode)
    if max_length is not None:
        slug = slug[:max_length]
    return slug


def paginate_results(request, *qs_serializers):
    """
    Custom pagination to handle multiple querysets and renderers.
    Supports serializing 1 to many different querysets. Based of DRF's
    LimitOffsetPagination. Useful when adding pagination to a regular
    APIView.

    qs_serializers - tuple of a queryset/array and respective serializer
    """
    limit = int(request.query_params.get('limit', api_settings.PAGE_SIZE))
    offset = int(request.query_params.get('offset', 0))

    count = 0
    cur_offset = offset
    out = []
    for qs, serializer in qs_serializers:
        len_func = ('__len__' if isinstance(qs, list) else 'count')
        qs_len = getattr(qs, len_func)()
        count += qs_len
        if (len(out) < limit):
            end_index = min([limit - len(out) + cur_offset, qs_len])
            qs = qs[cur_offset:end_index]
            if qs:
                out += serializer(qs, many=True).data
            cur_offset = max([cur_offset - end_index, 0])

    return OrderedDict([
        ('count', count),
        ('next', get_next_link(request, count)),
        ('previous', get_previous_link(request)),
        ('results', out),
    ])


def get_next_link(request, count):
    """ Generate URL of next page in pagination. """
    limit = int(request.query_params.get('limit', api_settings.PAGE_SIZE))
    offset = int(request.query_params.get('offset', 0))

    if offset + limit >= count:
        return None

    url = request.build_absolute_uri()
    url = replace_query_param(url, 'limit', limit)

    offset = offset + limit
    return replace_query_param(url, 'offset', offset)


def get_previous_link(request):
    """ Generate URL of previous page in pagination. """
    limit = int(request.query_params.get('limit', api_settings.PAGE_SIZE))
    offset = int(request.query_params.get('offset', 0))

    if offset <= 0:
        return None

    url = request.build_absolute_uri()
    url = replace_query_param(url, 'limit', limit)

    if offset - limit <= 0:
        return remove_query_param(url, 'offset')

    offset = offset - limit
    return replace_query_param(url, 'offset', offset)
