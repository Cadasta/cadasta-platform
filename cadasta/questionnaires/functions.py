import json

from django.utils import translation


def select_multilang_field_label(label):
    """This function checks if the supplied label is a valid JSON string so it
    can return the appropriate language label from the embedded JSON object.
    Otherwise the label is returned as is."""
    try:
        label_data = json.loads(label)
        lang_code = translation.get_language()
        lang_info = translation.get_language_info(lang_code)
        lang_name = lang_info['name']
        lang_native_name = lang_info['name_local']
        if lang_name in label_data:
            return label_data[lang_name]
        if lang_native_name in label_data:
            return label_data[lang_native_name]
        if lang_code in label_data:
            return label_data[lang_code]
        return label_data['default']
    except json.decoder.JSONDecodeError:
        return label
