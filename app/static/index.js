$('[data-toggle="popover"]').popover();

$('#button').click(function(){
   $("input[type='file']").trigger('click');
})


$('input:file').change(
    function(){
        if ($(this).val()) {
            $('#val').text(this.value.replace(/C:\\fakepath\\/i, ''))
            $('input:submit').attr('disabled',false);
            var file = this.files[0];
            uploadFile(file);
    }
});

function uploadFile(file){
    var formData = new FormData();
    formData.append('formData', file);
    $.ajax({
        url: '/upload',  //Server script to process data
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false
        //Ajax events
        //success: function(html){
        //    alert(html);
        //}
    });
}
