from django.forms import Select, SelectMultiple


class XLangSelect(Select):
    def __init__(self, xlang_labels, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xlang_labels = xlang_labels

    def set_xlang_labels(self, groups):
        # Iterate over all option groups
        for g in groups:

            # Each group is represented as a tuple:
            # (group name, list of options, index)
            # We want to iterate over all options in each group, hence g[1]
            for select in g[1]:
                xlang_labels = self.xlang_labels.get(select['value'], {})

                if not hasattr(xlang_labels, 'items'):
                    continue

                # converts the original xlang_labels to the required format
                labels_attrs = {'data-label-' + k: v
                                for k, v in xlang_labels.items()}
                select['attrs'].update(labels_attrs)

        return groups

    def optgroups(self, name, value, attrs=None):
        """
        We overwriting optgroups because we need to set multilingual labels
        for each option in the select field.
        """
        return self.set_xlang_labels(
            super().optgroups(name, value, attrs=attrs))


class XLangSelectMultiple(XLangSelect, SelectMultiple):
    pass
