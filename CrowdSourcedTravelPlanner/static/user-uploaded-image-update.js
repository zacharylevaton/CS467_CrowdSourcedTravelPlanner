$(document).ready(function() {
    var user_image = $('#user-uploaded-image');
    var filename_field = $('.form-control-file');

    $(filename_field).change(function() {
        $(user_image).empty();

        var reader = new FileReader();
        reader.onload = function (e) {
            $("<img />", {
                "src": e.target.result,
                "class": "img-rounded"
            }).appendTo(user_image);
        }

        user_image.show();
        reader.readAsDataURL($(this)[0].files[0]);
    });
});


