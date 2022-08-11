selected_html = '\
<div class="likeStar" data-liked="true">\
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-star-fill" viewBox="0 0 16 16">\
        <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>\
    </svg>\
</div>\
'

unselected_html = '\
<div class="likeStar" data-liked="false">\
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-star" viewBox="0 0 16 16">\
        <path d="M2.866 14.85c-.078.444.36.791.746.593l4.39-2.256 4.389 2.256c.386.198.824-.149.746-.592l-.83-4.73 3.522-3.356c.33-.314.16-.888-.282-.95l-4.898-.696L8.465.792a.513.513 0 0 0-.927 0L5.354 5.12l-4.898.696c-.441.062-.612.636-.283.95l3.523 3.356-.83 4.73zm4.905-2.767-3.686 1.894.694-3.957a.565.565 0 0 0-.163-.505L1.71 6.745l4.052-.576a.525.525 0 0 0 .393-.288L8 2.223l1.847 3.658a.525.525 0 0 0 .393.288l4.052.575-2.906 2.77a.565.565 0 0 0-.163.506l.694 3.957-3.686-1.894a.503.503 0 0 0-.461 0z"/>\
    </svg>\
</div>\
'
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
            if (result.like_status) {
                $(trElem).find('td > div.likeStar').html(selected_html);
            }
            else {
                $(trElem).find('td > div.likeStar').html(unselected_html);
            }
          },
          error: function(xhr, status, error) {
            console.log('Error in onLikeClick');
          },
          complete: function(xhr, status) {

          },
        });
        return false;
    }

    initializeTables();
    $('body').on('click', '.likeStar', onLikeClick);
} );