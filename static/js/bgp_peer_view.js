$(document).ready(function () {
    $('#loading_json').hide()
    load_data(false)
    $('#request_json').click(function (e) {
        load_data(true)

    });

    function load_data(delete_data) {
        $('#loading_json').show();
        if (delete_data === true) {
            Plotly.deleteTraces('graph', 0);
        }
        var date_start = $('#date_start').val();
        var date_end = $('#date_end').val();
        var uid = $('#uid').val();
        send_ajax_graph(date_start, date_end, uid)
    }



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
            if (index === 'uid') {
                var a = $('<a>');
                a.text('Ver historico');
                a.attr('href', '/reportes/bgp_neighbors/view/' + value)
                col.append(a)
            } else {
                col.text(String(value));
            }

            row.append(col);

        });
        $("" + table_id + " tbody").append(row)

    }

    function create_table_json_dict(table_id, table_data) {
        console.log(table_data)
        $(table_id + " tbody").empty();
        $(table_id + " thead").empty();
        add_table_header(table_data, table_id);
        $.each(table_data, function (key, row) {
            add_row_data_table(table_id, row);
        })

    }


    function create_bgp_graph(data, delete_data) {
        var layout = {
            hovermode: 'closest',
            font: {
                family: 'Raleway, sans-serif',
                size: 14
            },
            showlegend: false,
            xaxis: {
                tickangle: -90
            },
            yaxis: {
                zeroline: false,
                gridwidth: 2
            },
            bargap: 0.05
        };
        data['title'] = data[0]['name']
        var plotDiv = document.getElementById('graph')
        data['type'] = 'scatter'
        console.log(data)
        Plotly.plot(plotDiv, data, layout);
    }




    function send_ajax_graph(date_start, date_end, uid) {

        var url = "/reportes/bgp_neighbors/json/" + uid
        $.ajax({
            type: 'POST',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({date_start: date_start, date_end: date_end}),
            dataType: "json",

            url: url,
            success: function (data_json) {

                create_bgp_graph(data_json['traces'])
                create_table_json_dict('#bgp_peer_data', data_json['state_data'])
                $('#title_bgp').html(data_json['title'])

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