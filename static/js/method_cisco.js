$(document).ready(function () {

    $('#request_json').click(function (e) {

        var ip = $('#ip').val()
        var method = $('#method').val()
        send_ajax_graph(ip, method)

    })


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

    function send_ajax_graph(ip, method) {

        $.ajax({
            type: 'POST',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({method: method, ip: ip, params: ''}),
            dataType: "json",

            url: "/utilidades/metodos/cisco_json",
            success: function (traces) {
                create_table_json_dict("#device_data", traces)
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