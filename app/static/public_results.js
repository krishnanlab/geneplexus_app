$(document).ready( function () {
 
    $('#resultstable').DataTable({
        columnDefs: [
            {
                targets: [1, 2, 3],
                className: "dt-left"
            },
            {
                targets: [0, 4, 5],
                className: "dt-center"
            }
        ],
        pagingType: "full_numbers",
        initComplete: function(){
            $("#resultstable").show();
        }
    });


} );