$(document).ready( function () {
 
    $('#validatetable').DataTable({
        dom: '<"dom_wrapper fh-fixedHeader"Bf>tip',
        columnDefs: [
            {
                targets: [0, 1],
                className: "dt-left"
            },
            {
                targets: [2, 3, 4, 5],
                className: "dt-center"
            }
        ],
        pagingType: "full_numbers",
        buttons: ['pageLength','copy', 'excel', 'pdf' ],
        initComplete: function(){
            $("#validatetable").show();
        }
    });


} );