$(document).ready(function () {
    function getNumberOfForms(form, prefix) {
        var totalForms = form.find('[name="' + prefix + '-TOTAL_FORMS"]');
        return parseInt(totalForms.val())
    }

    function updateNumberOfForms(form, prefix, no) {
        var totalForms = form.find('[name="' + prefix + '-TOTAL_FORMS"]');
        totalForms.val(parseInt(totalForms.val()) + no)

        form.find('[name="' + prefix + '-INITIAL_FORMS"]').val(0);
    }

    function removeContact(event) {
        event.preventDefault();
        var target = $(event.target);
        if (target.tagName !== 'A') {
            target = target.parent();
        }
        var prefix = target.attr('data-prefix');

        var row = target.parents('tr');
        row.hide();
        row.find('[name="' + prefix + '-remove"]').val('on');
    }

    function replaceAttr(el, attr, prefix, newPrefix) {
        if (el.hasAttribute(attr)) {
            var val = el.getAttribute(attr);
            val = val.replace(new RegExp(prefix + '-[0-9]*', 'g'), newPrefix);
            el.setAttribute(attr, val);
        }
    }

    function addContact(event) {
        var target = $(event.target);
        var form = target.parents('form');
        var tbody = target.parents('table').children('tbody');

        var prefix = target.attr('data-prefix');
        var newRow = tbody.find("tr:first").clone(true);
        var newPrefix = prefix + '-' + getNumberOfForms(form, prefix);
        
        var td = newRow.children('td')
        for (var i = 0, ilen = td.length; i < ilen; i++) {
            var elements = $(td[i]).children();

            for (var j = 0, jlen = elements.length; j < jlen; j++) {
                var el = elements[j];

                ['name', 'id', 'data-prefix'].forEach(function(attr) {
                    replaceAttr(el, attr, prefix, newPrefix);
                });
                el.value = '';
            }
        }
        tbody.append(newRow.show());

        updateNumberOfForms(form, prefix, 1)
    }

    $('.remove-contact').click(removeContact);
    $('#add-contact').click(addContact);
});
