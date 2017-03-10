import random
import string
import django.utils.text as base_utils


ID_FIELD_LENGTH = 24

alphabet = string.ascii_lowercase + string.digits

chars_to_delete = 'l1o0'
replace_rules = dict.fromkeys(map(ord, chars_to_delete), None)
alphabet = alphabet.translate(replace_rules)

len_alphabet = len(alphabet) - 1


def byte_to_base32_chr(byte):
    return alphabet[byte & len_alphabet]


def random_id():
    rand_id = [random.randint(0, 0xFF) for i in range(ID_FIELD_LENGTH)]
    return ''.join(map(byte_to_base32_chr, rand_id))


def slugify(text, max_length=None, allow_unicode=False):
    slug = base_utils.slugify(text, allow_unicode=allow_unicode)
    if max_length is not None:
        slug = slug[:max_length]
    return slug
