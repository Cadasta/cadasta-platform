$(function() {
    $('.image-editor').cropit();

    $("input[name='new-image']").change(function() {
        // hide img tag with preview of existing stored image
        // in this way cropit displays selected image without overlapping
        $("#user-avatar").hide();
        $("#zoom").removeClass("hidden");
    });

    $('form').submit(function() {
        var imageData = $('.image-editor').cropit('export');
        $('.hidden-image-data').val(imageData);
    });
});
