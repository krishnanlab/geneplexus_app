$(document).ready(
    function(){
        $('[data-toggle="popover"]').popover();

        $("#network").attr('disabled',true);

        $('input:file').change(
            function(){
                if ($(this).val()) {
                    $('input:submit').attr('disabled',false);
                    $('#network').attr('disabled',false);
                    $("#network").val('BioGRID');
                }
            });
    });