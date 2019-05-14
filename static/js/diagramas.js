var network = undefined
var selected_edges = new Object()
var te_enabled = false
var color_scheme = true
function deselect_edge(edge) {


}

function enable_te() {
}


function get_xy_nodes() {
    var data = {}
    $.each(network.body.nodes, function (index, node) {
        data[index] = {x: node.x, y: node.y, net_device_uid: index}
    });
    return data;
}

function compute_array(edges) {
    var edges_array = [];
    Object.values(edges).forEach(function (edge) {
        edge_object = {from_id: edge.fromId, to_id: edge.toId, to_ip: edge.ip_to, from_ip: edge.ip_from}
        edges_array.push(edge_object);
    });

    console.log(edges_array)
    return edges_array
}


function display_te(data) {
    var a = $('#te_a');
    var b = $('#te_b');
    a.empty();
    b.empty();
    var ab_hops = data['a-b'];
    var ba_hops = data['b-a'];
    var label_a = network.body.nodes[data['a']].options.label;
    var label_b = network.body.nodes[data['b']].options.label;
    a.html("<h5>" + label_a + "</h5><br>" + get_te_hops(ab_hops));
    b.html("<h5>" + label_b + "</h5><br>" + get_te_hops(ba_hops));

}

function get_te_hops(hops) {
    var text = ""
    hops.forEach(function (hop) {
        text += "next-address " + hop + "<br>"
    })

    return text

}


$(document).ready(function () {
        var saved = $('#saved').val();
        var date = $('#date').val();
        var network_name = $('#network').val();


        send_ajax_diag_network(date, network_name, saved);


        $("#save_xy").click(function (e) {


            var network = $('#network').val();
            save_xy(network, get_xy_nodes())

        });

        $("#ospf_form").submit(function (e) {
            return false;
        });

        $("#send_path").hide()
        $('#enable_te').change(function () {
            if (this.checked) {
                $("#send_path").show()
                te_enabled = true
            } else {
                $("#send_path").hide()
                te_enabled = false
            }

        });

        $("#send_path").click(function (e) {

            send_path(compute_array(selected_edges));


        });

        $("#request_json").click(function (e) {
            selected_edges = new Object()
            $('#loading_json').show();
            var saved = $('#saved').val();
            var date = $('#date').val();
            var network = $('#network').val();
            send_ajax_diag_network(date, network, saved);


        });

        $("#change_color").click(function (e) {

            if (color_scheme) {
                usage_color(network.body.edges);
                color_scheme = false
            } else {
                interface_type_color(network.body.edges)
                color_scheme = true
            }
            network.redraw()

        });

        function create_network(traces) {
            var container = document.getElementById('mynetwork');
            var data = {
                nodes: new vis.DataSet(traces['nodes']),
                edges: new vis.DataSet(traces['edges']),
                options: traces['options']
            };
            var options = {};
            network = new vis.Network(container, data, options);


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


        function send_ajax_diag_network(date, network_name, saved) {

            $.ajax({
                type: 'POST',
                contentType: 'application/json;charset=UTF-8',
                data: JSON.stringify({date: date, network: network_name, saved: saved}),
                dataType: "json",

                url: "/diagramas/prueba_json",
                success: function (traces) {
                    console.log(traces)
                    create_network(traces);


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

        function send_path(edges) {

            $.ajax({
                type: 'POST',
                contentType: 'application/json;charset=UTF-8',
                data: JSON.stringify({data: edges}),
                dataType: "json",

                url: "/diagramas/te_json",
                success: function (data) {

                    display_te(data);
                    alert("CRU CRU")

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


        function save_xy(network_name, data) {

            $.ajax({
                type: 'POST',
                contentType: 'application/json;charset=UTF-8',
                data: JSON.stringify({network: network_name, data: data}),
                dataType: "json",

                url: "/diagramas/save_xy",
                success: function (traces) {
                    console.log(traces)


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

