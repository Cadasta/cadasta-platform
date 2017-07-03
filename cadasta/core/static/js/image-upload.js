$(function() {
    $('.image-editor').cropit();
    $('form').submit(function() {
    var imageData = $('.image-editor').cropit('export');
    $('.hidden-image-data').val(imageData);
    });
});
