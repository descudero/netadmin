$(document).ready(function () {
    $('#loading_json').hide()

    $('#request_json').click(function (e) {
        $('#loading_json').show();
        $("#interfaces_data tbody").empty();
        $("#interfaces_data thead").empty();
        var initial_date = $('#initial_date').val();
        var end_date = $('#end_date').val();
        var cantidad_interfaces = $('#cantidad_interfaces').val();
        var grupo_interfaces = $('#grupo_interfaces').val();
        send_ajax(initial_date, end_date, cantidad_interfaces, grupo_interfaces)

    });


    function add_table_header(table_data, table_id) {
        console.log("add table header")
        console.log('' + table_id + ' thead')
        var row = table_data[Object.keys(table_data)[0]]
        console.log(table_data);
        var row_mark = $('' + table_id + ' thead').append($("<tr>"))
        $.each(row, function (key, value) {
            row_mark.append($("<th>").text(String(key)));
        });
    }

    function add_row_data_table(table_id, row_data) {
        var row = $('<tr>');
        $.each(row_data, function (index, value) {
            var col = $('<td>');
            col.text(String(value));
            row.append(col);

        });
        $("" + table_id + " tbody").append(row)

    }

    function create_table_json_dict(table_id, table_data) {
        console.log(table_data)
        add_table_header(table_data, table_id);
        $.each(table_data, function (key, row) {
            add_row_data_table(table_id, row);
        })

    }

    function send_ajax(initial_date, end_date, cantidad_interfaces, grupo_interfaces) {
        ;
        $.ajax({
            type: 'POST',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({
                initial_date: initial_date,
                end_date: end_date,
                cantidad_interfaces: cantidad_interfaces,
                grupo_interfaces: grupo_interfaces
            }),
            dataType: "json",

            url: "/reportes/interfaces/regionales/json",
            success: function (traces) {
                create_table_json_dict("#interfaces_data", traces)
                $('#loading_json').hide()
            },
            error: function (xhr, ajaxOptions, thrownError) {
                alert(xhr.status);
                alert(thrownError);
            },
            complete: function () {
                // Handle the complete event

            }
        });


    }

});