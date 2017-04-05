$('input#id_email').change(function() {
    const current_email = $(this).attr('value');
    const new_email = $(this).val();

    if (current_email !== new_email) {
        $('#group_password').removeClass('hide');
        $('#id_password').attr('data-parsley-required', 'true');
    } else {
        $('#group_password').addClass('hide');
        $('#id_password').removeAttr('data-parsley-required');
    }
});
