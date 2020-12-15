$('[data-toggle="popover"]').popover();

$('#geneButton').click(function(){
   $("input[type='file']").trigger('click');
})


$('input:file').change(
    function(){
        if ($(this).val()) {
            $('#filename').text(this.value.replace(/C:\\fakepath\\/i, ''))
            $('input:submit').attr('disabled',false);
            $('#geneBtn').prop('disabled',true);
            console.log()
            var file = this.files[0];
            uploadFile(file);
    }
});

function uploadFile(file){
    var formData = new FormData();
    formData.append('formData', file);
    $.ajax({
        url: '/uploadgenes',  //Server script to process data
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false
        //Ajax events
        //success: function(html){
        //    alert(html);
        //}
    });
    event.preventDefault();
}


function saveGenes(){
    var genes = $('#enterGenes').val();

    $.ajax({
        data: {
            genes: genes
        },
        type: 'POST',
        url: '/postgenes',
        success: function(data) {
            console.log(data);
            console.log(data.success);
            $('#geneModal').modal('hide');
            $('input:submit').attr('disabled',false);
            $("#geneButton").css("pointer-events", "none");
            $('#filename').empty();
        }
    });
    event.preventDefault();
}

function clearInput(){
    $.ajax({
        type: 'POST',
        url: '/clearinput',
        success: function(data) {
            console.log(data.success);
            $('input:submit').attr('disabled',true);
            $('#filename').empty();
            $('#geneBtn').prop('disabled', false);
            $("#geneButton").css("pointer-events", "auto");
        }
    });
    event.preventDefault();
}


function appendHash(){
    var jobname = $('#job').val();
    $.ajax({
        data: {
            jobname: jobname
        },
      type: 'POST',
      url: "/appendhash",

      success: function(data){
        console.log(data.success);
        $('#job').val(data.jobname);
      }
    });
    event.preventDefault();
};


function runBatch(){
    var jobname = $('#job').val();
    var nettype = $('#network').val();
    var features = $('#features').val();
    var GSC = $('#negativeclass').val();

    $.ajax({
        data: {
            jobname: jobname,
            network: nettype,
            feature: features,
            negativeclass: GSC,
        },
      type: 'POST',
      url: "/runbatch",
      success: function(data){
        console.log(data.success);
      }
    });
    event.preventDefault();
};