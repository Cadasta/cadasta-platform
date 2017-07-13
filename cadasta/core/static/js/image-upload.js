$(function() {
    var URL_DEFAULT_AVATAR = '/static/img/avatar_sm.jpg';
    var URL_USER_AVATAR = $('#user-avatar').attr('src');
    var avatarChanged = false;

    $('#image-editor').cropit({
        onFileChange: function() {
            avatarChanged = true;
            $("#user-avatar").hide();
        },
        onZoomDisabled: function() {
            $("#zoom").addClass("hidden");
        },
        onZoomEnabled: function() {
            $("#zoom").removeClass("hidden");
        },
        smallImage: 'stretch',
    });

    $("#delete").click(function() {
        avatarChanged = true;
        $("#upload").val("");
        $('#image-editor').cropit('imageSrc', URL_DEFAULT_AVATAR);
    });

    $("#undo").click(function() {
        avatarChanged = false;
        $("#upload").val("");
        $('#image-editor').cropit('imageSrc', URL_USER_AVATAR);
    });

    $('form').submit(function() {
        if (avatarChanged) {
            var imageData = $('#image-editor').cropit('export');
            $('#hidden-image-data').val(imageData);
        }
    });
});