$(document).ready(function () {
    $('#loading_json').hide()
    load_data(false)
    $('#request_json').click(function (e) {
        load_data(true)

    });

    function load_data(delete_data) {
        $('#loading_json').show();
        if (delete_data === true) {
            Plotly.deleteTraces('graph', [-2, -1]);
        }
        var date_start = $('#date_start').val();
        var date_end = $('#date_end').val();
        var uid = $('#uid').val();
        send_ajax_graph(date_start, date_end, uid)
    }


    function create_interface_graph(data_interface) {
        var layout = {
            title: {
                text: data_interface['name'],
                font: {
                    family: 'Courier New, monospace',
                    size: 24
                },
            },
            hovermode: 'closest',
            font: {
                family: 'Raleway, sans-serif',
                size: 14
            },
            showlegend: true,
            xaxis: {
                tickangle: -90,
                tickformat: '%m-%d-%H:%M'
            },
            yaxis: {
                zeroline: true,
                gridwidth: 2,
                tickvals: [-100, -90, -80, -70, -60, -50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                range: [-100, 100],
                ticktext: [100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                range: [-100, 100],
                showticksuffix: 'all',
                ticksuffix: '%',
            },
            bargap: 0.05
        };


        var data_out = data_interface['out']
        data_out['name'] = '% out_rate'
        var data_in = data_interface['in']
        data_in['name'] = '% in_rate'
        var traces = [data_out, data_in]

        var plotDiv = document.getElementById('graph')
        var plot = Plotly.plot(plotDiv, traces, layout);

    }


    function send_ajax_graph(date_start, date_end, uid) {

        var url = "/interface/json"
        $.ajax({
            type: 'POST',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({date_start: date_start, date_end: date_end, uid: uid}),
            dataType: "json",

            url: url,
            success: function (data_json) {
                console.log(data_json)
                create_interface_graph(data_json)

                $('#title_interface').html(data_json['name'])

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