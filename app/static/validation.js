function appendPrefix(){
    var jobname = $('#job').val();
    var prefix = $('#prefix').val();
    $.ajax({
        data: {
            jobname: jobname,
            prefix: prefix
        },
      type: 'POST',
      url: "/appendprefix",

      success: function(data){
        console.log(data.success);
        $('#job').val(data.jobname);
      }
    });
    event.preventDefault();
};

// run batch now works through same flask route as run local
// function runBatch(){
//     var jobname = $('#job').val();
//     var nettype = $('#network').val();
//     var features = $('#features').val();
//     var GSC = $('#negativeclass').val();

//     $.ajax({
//         data: {
//             jobname: jobname,
//             network: nettype,
//             feature: features,
//             negativeclass: GSC,
//         },
//       type: 'POST',
//       url: "/runbatch",
//       success: function(data){
//         console.log(data.success);
//       }
//     });
//     event.preventDefault();
// };