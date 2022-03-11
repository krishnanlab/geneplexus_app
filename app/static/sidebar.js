$('#insertGeneButton').click(function(){
    $("input[type='file']").trigger('click');
});

$('#insertGenesInput').change(
    function(){
        if ($(this).val() != '') {
            console.log()
            var file = this.files[0];
            uploadFile(file);
    }
});

$('#clearButton').click(function(){
    $('#enterGenes').val('');
})

function uploadFile(file){
    var formData = new FormData();
    formData.append('formData', file);
    $.ajax({
        url: '/uploadgenes',  //Server script to process data
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        success: function(jsonReturn){
            $('#enterGenes').val(jsonReturn['data'].join('\n'));
        },
        complete: function(request, message){
            $('#insertGenesInput').replaceWith($("#insertGenesInput").val('').clone(true))
        }
    });
}

function sampleGenes(){
    var your_array = ['CCNO','CENPF','LRRC56','ODAD3','DNAAF1','DNAAF6','DNAAF4','DNAH5','DNAH9','CFAP221','RSPH9',
    'FOXJ1','LRRC6','GAS2L2','DNAH1','GAS8','DNAI1','STK36','MCIDAS','RSPH4A','DNAAF3','DNAJB13','CCDC103','NME8',
    'ZMYND10','HYDIN','DNAAF5','CCDC40','ODAD2','DNAAF2','IFT122','INPP5E','CFAP298','DNAI2','SPAG1','SPEF2','ODAD4',
    'DNAL1','RSPH3','OFD1','CFAP300','CCDC65','DNAH11','RSPH1','DRC1','ODAD1'];
    var textarea = document.getElementById("enterGenes");
    textarea.value = your_array.join("\n");
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
}

$('#prefix').on('change keyup blur', function(){
    prefix = $('#prefix').val()
    $.ajax({
        type: 'POST',
        url: '/get_slugified_text',
        contentType: 'application/json',
        data: JSON.stringify({
            'prefix': prefix
        }),
        success: function(data) {
            if (data.prefix_too_long){
                $('#char_limit').text('Your input is ' + data.too_long_by + ' characters too long. It will be truncated on submit');
            }
            else{
                $('#char_limit').text('');
            }
        }
    })
});

$('#runbatch').click(function(e) {
    setTimeout(function () { disableButton(); }, 0);
});

function disableButton() {
    $('#runbatch').prop('disabled', true);
}
