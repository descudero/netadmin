var network = undefined
var selected_edges = new Object()
var te_enabled = false
var color_scheme = true


function get_xy_nodes() {
    var data = {}
    $.each(network.body.nodes, function (index, node) {
        data[index] = {x: node.x, y: node.y, net_device_uid: index}
    });
    return data;
}

$(document).ready(function () {
        var saved = $('#saved').val();
        var date = $('#date').val();
        var network_name = $('#network').val();
        var data_intervals


        $("#ospf_form").submit(function (e) {
            return false;
        });


        $("#request_json").click(function (e) {
            selected_edges = new Object()
            $('#loading_json').show();
            var tipo_periodo = $('#tipo_periodo').val();
            var date = $('#date').val();
            var network = $('#network').val();
            send_ajax_diag_network_interval(date, network, tipo_periodo);


        });

        $("#change_color").click(function (e) {
            change_scheme()
        });
        $("#horas").change(function (e) {
            slider_change($(this).val())
        });

        function change_scheme() {

            if (color_scheme) {
                usage_color(network.body.edges);
                color_scheme = false
            } else {
                interface_type_color(network.body.edges)
                color_scheme = true
            }
            network.redraw()

        }

        function slider_change(index) {
            var data = data_intervals[index]

            $('#titulo').text(" MAX OUPUT RATE " + data['period'])
            create_network(data['vs'])
            color_scheme = true
            change_scheme()
        }

        function create_network(traces) {
            var fix_scale = false;
            if (network !== undefined) {
                fix_scale = true;
                var position = network.getViewPosition();
                var scale = network.getScale();
            }
            var container = document.getElementById('mynetwork');
            var data = {
                nodes: new vis.DataSet(traces['nodes']),
                edges: new vis.DataSet(traces['edges']),
                options: traces['options']
            };
            var options = {};
            network = new vis.Network(container, data, options);
            if (fix_scale) {
                network.moveTo({position: position, scale: scale});
            }



            network.on("click", function (params) {
                if (te_enabled) {
                    var edge_id = this.getEdgeAt(params.pointer.DOM);
                    if (selected_edges.hasOwnProperty(edge_id)) {
                        this.body.edges[edge_id].options.color.color = this.body.edges[edge_id].prev_color
                        this.body.edges[edge_id].options.width = 2
                        delete selected_edges[edge_id]
                    } else {
                        this.body.edges[edge_id].prev_color = this.body.edges[edge_id].options.color.color
                        this.body.edges[edge_id].options.color.color = '#000000'
                        this.body.edges[edge_id].options.width = 5
                        selected_edges[edge_id] = this.body.edges[edge_id]
                    }

                    this.redraw()
                }
            });


        }


        function change_edge_color(edge, key_color) {
            edge.options.color.color = edge[key_color]
        }

        function change_edge_width(edge, width_key) {
            edge.options.width = edge[width_key]
        }

        function usage_color(edges) {
            $.each(edges, function (index, edge) {
                change_edge_color(edge, 'cusage');
                change_edge_width(edge, 'wusage')
            });
        }

        function interface_type_color(edges) {
            $.each(edges, function (index, edge) {
                change_edge_color(edge, 'interface_type')
                change_edge_width(edge, 'winterface_type')
            });
        }


        function send_ajax_diag_network_interval(date, network_name, tipo_periodo) {

            $.ajax({
                type: 'POST',
                contentType: 'application/json;charset=UTF-8',
                data: JSON.stringify({date: date, network: network_name, tipo_periodo: tipo_periodo}),
                dataType: "json",

                url: "/diagramas/ospf_json_intervalos",
                success: function (traces) {
                    data_intervals = traces
                    $("#horas").val(0)
                    console.log(data_intervals)
                    slider_change(0);


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


    }
)
;

