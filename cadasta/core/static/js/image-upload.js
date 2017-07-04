$(function() {
    $("input[name='zoom']").hide();
    $('.image-editor').cropit();

    $("input[name='new-image']").change(function() {
    $("input[name='zoom']").show();
    });

    $('form').submit(function() {
    var imageData = $('.image-editor').cropit('export');
    $('.hidden-image-data').val(imageData);
    });
});
