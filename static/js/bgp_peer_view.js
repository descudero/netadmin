$(document).ready(function () {
    $('#loading_json').hide()
    load_data()
    $('#request_json').click(function (e) {
        load_data()

    });

    function load_data() {
        $('#loading_json').show();
        $("#bgp_peers_data tbody").empty();
        $("#bgp_peers_data thead").empty();
        var initial_date = $('#date_start').val();
        var end_date = $('#date_end').val();
        var uid = $('#uid').val();
        send_ajax_graph(initial_date, end_date, uid)
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
        add_table_header(table_data, table_id);
        $.each(table_data, function (key, row) {
            add_row_data_table(table_id, row);
        })

    }

    function send_ajax(initial_date, end_date, uid) {
        ;
        $.ajax({
            type: 'POST',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({
                initial_date: initial_date,
                end_date: end_date, uid: uid
            }),
            dataType: "json",

            url: "/reportes/bgp_neighbors/json/",
            success: function (traces) {
                console.log(traces)
                create_table_json_dict("#bgp_peers_data", traces)
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


    function send_ajax_graph(date_start, date_end, uid) {
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
        var url = "/reportes/bgp_neighbors/json/" + uid
        $.ajax({
            type: 'POST',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({date_start: date_start, date_end: date_end}),
            dataType: "json",

            url: url,
            success: function (traces) {

                layout['title'] = traces[0]['name']
                var plotDiv = document.getElementById('graph')
                traces['type'] = 'scatter'
                console.log(traces)
                Plotly.plot(plotDiv, traces, layout);


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