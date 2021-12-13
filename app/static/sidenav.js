$('#prefix').bind('keyup change blur', function () {
    var val = $(this).val();
    $.ajax({
        type: 'POST',
        url: '/set_prefix',
        contentType: "application/json",
        data: JSON.stringify(
            {value: val}
        )
    });

})

$('#network').bind('keyup change blur', function () {
    var val = $(this).val();
    $.ajax({
        type: 'POST',
        url: '/set_network',
        contentType: "application/json",
        data: JSON.stringify(
            {value: val}
        )
    });
})

$('#features').bind('keyup change blur', function () {
    var val = $(this).val();
    $.ajax({
        type: 'POST',
        url: '/set_features',
        contentType: "application/json",
        data: JSON.stringify(
            {value: val}
        )
    });
})

$('#negativeclass').bind('keyup change blur', function () {
    var val = $(this).val();
    $.ajax({
        type: 'POST',
        url: '/set_negativeclass',
        contentType: "application/json",
        data: JSON.stringify(
            {value: val}
        )
    });
})

$('#notifyaddress').bind('keyup change blur', function () {
    var val = $(this).val();
    $.ajax({
        type: 'POST',
        url: '/set_notifyaddress',
        contentType: "application/json",
        data: JSON.stringify(
            {value: val}
        )
    });
})

