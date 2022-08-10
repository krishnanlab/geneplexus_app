$(document).ready( function () {
    resultstable = null;
    function initializeTables() {
        var num_cols = $("#resultstable tr th").length;
        if (num_cols == 6) {
            resultstable = $('#resultstable').DataTable({
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
        }
        if (num_cols == 5) {
            resultstable = $('#resultstable').DataTable({
                columnDefs: [
                    {
                        targets: [1, 2, 3],
                        className: "dt-left"
                    },
                    {
                        targets: [0, 4],
                        className: "dt-center"
                    }
                ],
                pagingType: "full_numbers",
                initComplete: function(){
                    $("#resultstable").show();
                }
            });
        }
    }

    function onLikeClick() {
        trElem = $(this).closest('tr');
        var resultid = trElem.find('td > a').text();
        var isliked = trElem.find('td > div.likeStar')[0].dataset.liked.toLowerCase() == "true";

        console.log(resultid);
        console.log(isliked);
        $.ajax({
            data: JSON.stringify({
                resultid: resultid,
                liked: isliked,
            }),
          type: 'POST',
          url: "/like_result",
          contentType: "application/json",
          dataType: 'json',
          success: function(result, status, xhr){
            console.log('Successful in onLikeClick');
          },
          error: function(xhr, status, error) {
            console.log('Error in onLikeClick');
          },
          complete: function(xhr, status) {

          },
        });
    }

    initializeTables();
    $('body').on('click', '.likeStar', onLikeClick);
} );