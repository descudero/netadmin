$(document).ready(function () {
    var saved = $('#saved').val();
    var date = $('#date').val();
    var network = $('#network').val();
    send_ajax_diag_network(date, network, saved);

    $("#request_json").click(function (e) {
        $('#loading_json').show();
        var saved = $('#saved').val();
        var date = $('#date').val();
        var network = $('#network').val();
        send_ajax_diag_network(date, network, saved);


    });


    function send_ajax_diag_network(date, network, saved) {

        $.ajax({
            type: 'POST',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({date: date, network: network, saved: saved}),
            dataType: "json",

            url: "/diagramas/prueba_json",
            success: function (traces) {

                var container = document.getElementById('mynetwork');
                var data = {
                    nodes: new vis.DataSet(traces['nodes']),
                    edges: new vis.DataSet(traces['edges']),
                    options: traces['options']
                };
                var options = {};
                var network = new vis.Network(container, data, options);
                network.on("stabilizationIterationsDone", function () {
                    network.setOptions({physics: false});
                });


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

