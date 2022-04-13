$(document).ready( function () {
    $('#probstable').DataTable({
        "lengthChange": true,
        dom: '<"dom_wrapper fh-fixedHeader"Bf>tip',
        buttons: ['pageLength','copy', 'excel', 'pdf', {
            text: 'TSV',
            extend: 'csvHtml5',
            fieldSeparator: '\t',
            extension: '.tsv'
        }],
        fixedHeader: true,
        order: [[ 0, "asc" ]],
        columnDefs: [
        
            {
                
                targets: [ 0 ],
                width: '4%',
                className: "dt-right"
            },
            {
                
                targets: [1],
                className: "dt-left",
                render: function (data, type, row, meta) {
                    if(type === 'display') {
                        data = '<a target="_blank" href="https://www.ncbi.nlm.nih.gov/gene/' + encodeURIComponent(data) + '">' + data + '</a>';
                    }
                    return data;
                }

            },
            {
                
                targets: [2],
                width: '14%',
                className: "dt-left"
            },
            {
                
                targets: [3],
                width: '26%',
                className: "dt-left"
            },
            {
                
                targets: [ 4 ],
                width: '14%',
                className: "dt-right",
                defaultOrder: true,
                sortOrder: 'desc',
                render: function (data, type, full) {
                    return parseFloat(data).toFixed(2);
                }
            },
            {
                
                targets: [ 5 ],
                width: '14%',
                className: "dt-center"
            },
            {
                
                targets: [ 6 ],
                width: '14%',
                className: "dt-center"
            }  ,
        ],
        pagingType: "full_numbers",
        initComplete: function(){
            $("#probstable").show();
            $('body').removeClass("loading");
        }
    });



    $('#gotable').DataTable({
        dom: '<"dom_wrapper fh-fixedHeader"Bf>tip',
        buttons: ['pageLength','copy', 'excel', 'pdf', {
            text: 'TSV',
            extend: 'csvHtml5',
            fieldSeparator: '\t',
            extension: '.tsv'
        }],
        fixedHeader: true,
        order: [[ 0, "asc" ]],
        columnDefs: [
            {
                targets: [0],
                className: "dt-right all"

            },
            {
                responsivePriority: 1,
                targets: [1],
                className: "dt-left all",
                render: function (data, type, row, meta) {
                    if(type === 'display') {
                        data = '<a target="_blank" href="http://amigo.geneontology.org/amigo/term/' + encodeURIComponent(data) + '">' + data + '</a>';
                    }
                    return data;
                }
            },
            {
                targets: [2],
                className: "dt-left all"
            },
            {
                targets: [3],
                className: "dt-right all",
                defaultOrder: true,
                sortOrder: 'desc',
                render: function (data, type, full) {
                    return parseFloat(data).toFixed(2);
                }
            },
        ],
        pagingType: "full_numbers",
        initComplete: function(){
            $("#gotable").show();
        }
    });

    $('#distable').DataTable({
        dom: '<"dom_wrapper fh-fixedHeader"Bf>tip',
        buttons: ['pageLength','copy', 'excel', 'pdf', {
            text: 'TSV',
            extend: 'csvHtml5',
            fieldSeparator: '\t',
            extension: '.tsv'
        } ],
        fixedHeader: true,
        order: [[ 0, "asc" ]],
        columnDefs: [
            {
                targets: [0],
                className: "dt-right all"

            },
            {
                targets: [1],
                className: "dt-left",
                render: function (data, type, row, meta) {
                    if(type === 'display') {
                        data = '<a target="_blank" href="https://disease-ontology.org/?id=' + encodeURIComponent(data) + '">' + data + '</a>';
                    }
                    return data;
                }
            },
            {
                targets: [2],
                className: "dt-left"
            },
            {
                targets: [3],
                className: "dt-right",
                defaultOrder: true,
                sortOrder: 'desc',
                render: function (data, type, full) {
                    return parseFloat(data).toFixed(2);
                }
            },
        ],
        pagingType: "full_numbers",
        initComplete: function(){
            $("#distable").show();
        }
    });

    $('#validateresults').DataTable({
        dom: '<"dom_wrapper fh-fixedHeader"Bf>tip',
        columnDefs: [
            {
                targets: [0, 1],
                className: "dt-left"
            },
            {
                targets: [2],
                className: "dt-center"
            }
        ],
        pagingType: "full_numbers",
        buttons: ['pageLength','copy', 'excel', 'pdf', {
            text: 'TSV',
            extend: 'csvHtml5',
            fieldSeparator: '\t',
            extension: '.tsv'
        }],
        initComplete: function(){
            $("#validateresults").show();
        }
    });

} );