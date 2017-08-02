$(function() {
    var URL_DEFAULT_AVATAR = '/static/img/avatar_sm.jpg';

    $('.file-remove').attr('role', 'button');
    $('.file-remove').addClass('btn btn-danger btn-sm');
    $('.file-remove').text('Remove');

    $('.file-input').change(function(event) {
        var accepted = $(this).parents('.s3-buckets').attr('data-accepted-types');

        var file = event.target.files.length && event.target.files[0];

        if (file && (!accepted || accepted.split(',').indexOf(file.type) !== -1)) {
            var reader = new FileReader();
            reader.onload = function(e) {
                $('#avatar-preview').attr('src', e.target.result);
            };
            reader.readAsDataURL(file);
        }
    });

    $('.file-remove').click(function() {
        $('#avatar-preview').attr('src', URL_DEFAULT_AVATAR);
    });
});

