$(document).ready(function(data){
    /*
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            html: true
        })
    });
    */
    $("[data-bs-toggle=popover]")
    .popover({ html: true})
        .on("focus", function () {
            $(this).popover("show");
        }).on("focusout", function () {
            var _this = this;
            if (!$(".popover:hover").length) {
                $(this).popover("hide");
            }
            else {
                $('.popover').mouseleave(function() {
                    $(_this).popover("hide");
                    $(this).off('mouseleave');
                });
            }
        });
});