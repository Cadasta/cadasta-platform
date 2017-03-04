$(document).ready(function() {
    'use strict';
    $("form [type=submit]").click(function(event) {
        var button = event.target;
        var $validator = $("[data-parsley-validate]").parsley();
        var formIsValid = $validator.isValid();

        if (formIsValid) {
            button.form.submit();
            button.disabled = true;
        };
    });
});
