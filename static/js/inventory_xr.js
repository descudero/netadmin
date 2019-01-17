String.prototype.replaceAll = function (search, replacement) {
    var target = this;
    return target.split(search).join(replacement);
};

$(document).ready(function () {
    $('.loading_json').hide()
    update_tables($('#attr').val())

    $('#attr').change(function (event) {
        update_tables($('#attr').val())

    })


    function update_tables(attr) {
        $(".device_ip").each(function () {
            var ip = ($(this).val())

            send_ajax_table(ip, attr)

        });
    }

    function add_table_header(table_data, table_id) {

        var row = table_data[0]
        var row_mark = $('' + table_id + " thead").append($("<tr>"))

        $.each(row, function (key, value) {
            console.log(key);
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
        $(table_id + " tbody").empty();
        $(table_id + " thead").empty();
        add_table_header(table_data, table_id);
        $.each(table_data, function (key, row) {
            add_row_data_table(table_id, row);
        })

    }

    function send_ajax_table(ip, attr) {
        ;
        $.ajax({
            type: 'POST',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({ip: ip, attr: attr}),
            dataType: "json",

            url: "/reportes/inventario/xr_json",
            success: function (traces) {

                create_table_json_dict("#" + ip.replaceAll(".", ""), traces)
                $('.loading_json').hide()
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            },
            complete: function () {
                // Handle the complete event

            }
        });


    }

});