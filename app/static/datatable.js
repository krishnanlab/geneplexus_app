$(document).ready( function () {
    $('#probstable').DataTable({
        dom: '<"dom_wrapper fh-fixedHeader"Bf>tip',
        buttons: ['copy', 'excel', 'pdf' ],
        fixedHeader: true,
        columnDefs: [
            {
                targets: [0, 2],
                className: "dt-left"
            },
            {
                targets: [ 3 ],
                className: "dt-right",
                render: function (data, type, full) {
                    return parseFloat(data).toFixed(2);
                }
            },
            {
                targets: [ 4 ],
                className: "dt-center"
            }
        ],
        pagingType: "full_numbers",
        initComplete: function(){
            $("#probstable").show();
        }
    });

    var probstable = $('#probstable').DataTable();

    $('#probstable tbody').on('click', 'tr', function () {
        var data = probstable.row( this ).data();
        alert( 'You clicked on Entrez '+data[0]+'\'s row' );
    });


    $('#gotable').DataTable({
        dom: '<"dom_wrapper fh-fixedHeader"Bf>tip',
        buttons: ['copy', 'excel', 'pdf' ],
        fixedHeader: true,
        columnDefs: [
            {
                targets: [0, 1],
                className: "dt-left"
            },
            {
                targets: [2],
                className: "dt-right"
            }
        ],
        pagingType: "full_numbers",
        initComplete: function(){
            $("#gotable").show();
        }
    });

    $('#distable').DataTable({
        dom: '<"dom_wrapper fh-fixedHeader"Bf>tip',
        buttons: ['copy', 'excel', 'pdf' ],
        fixedHeader: true,
        columnDefs: [
            {
                targets: [0, 1],
                className: "dt-left"
            },
            {
                targets: [2],
                className: "dt-right"
            }
        ],
        pagingType: "full_numbers",
        initComplete: function(){
            $("#distable").show();
        }
    });
} );