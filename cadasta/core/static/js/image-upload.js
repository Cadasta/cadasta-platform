$(function() {
    var URL_DEFAULT_AVATAR = '/static/img/avatar_sm.jpg';
    var URL_USER_AVATAR = $('#user-avatar').attr('src');
    var avatarChanged = false;
    var avatarReady = false;
    var hideZoomRange = false;

    function setVisibilityZoomRange(hideZoomRange) {
        if (hideZoomRange) {
            $("#zoom").addClass("hidden");
        } else {
            $("#zoom").removeClass("hidden");
        }
    }

    function fetchBase64ForImage(imageUrl, imageWidth, imageHeight, callback) {
        var image = new Image();
        image.onload = function() {
            var canvas = document.createElement("canvas");
            canvas.width = imageWidth;
            canvas.height = imageHeight;
            var ctx = canvas.getContext("2d");
            ctx.drawImage(this, 0, 0);
            var dataURL = canvas.toDataURL("image/png");
            callback(dataURL);
        };
        image.src = imageUrl;
    }

    function setProfilePictureToDefaultAvatar() {
        avatarReady = false;
        avatarChanged = true;
        fetchBase64ForImage(URL_DEFAULT_AVATAR, 200, 200, function(imageData) {
            $('.hidden-image-data').val(imageData);
            $('.image-editor').cropit('imageSrc', URL_DEFAULT_AVATAR);
            avatarReady = true;
            hideZoomRange = true;
        });
    }

    function setProfilePictureToUploadedAvatar() {
        avatarReady = false;
        avatarChanged = true;
        $("#user-avatar").hide();
        var imageData = $('.image-editor').cropit('export');
        $('.hidden-image-data').val(imageData);
        setVisibilityZoomRange(hideZoomRange);
        avatarReady = true;
        hideZoomRange = false;
    }

    $('.image-editor').cropit({
        onImageLoaded: setProfilePictureToUploadedAvatar
    });

    $("#delete").click(function() {
        setProfilePictureToDefaultAvatar();
    });

    $("#undo").click(function() {
        $('.image-editor').cropit('imageSrc', URL_USER_AVATAR);
    });

    $('form').submit(function() {
        return !avatarChanged || avatarReady;
    });
});