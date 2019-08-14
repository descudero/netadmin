$(document).ready(function () {
    var groups = ['PROVEEDORES_TIER_1_INTERNET', 'CONEXIONES_DIRECTAS_PEERING',
        'SERVIDORES_CACHE_TERCEROS', 'TRUNCALES_SUBMARINAS_MPLS', 'BGPS_DIRECTOS']
    var column_order = ['host', 'inter', 'description', 'l1a', 'l1p', 'l3a', 'l3p', 'data_flow', 'in_gbs', 'out_gbs', 'util_in', 'util_out', 'uid']
    $('#loading_json').hide()
    load_tables();
    load_data();
    //load_graph();
    $("#form_send").submit(function (e) {
        $("#titulo").empty().text('REPORTE INTERNET ' + $("#initial_date").val() + " a " + $("#end_date").val())
        load_data();
        //load_graph();
        return false;

    });

    function load_graph() {
        var date_start = $("#initial_date").val();
        var date_end = $("#end_date").val();
        $(".group_name").each(function () {
            send_ajax_graph($(this).val(), date_start, date_end, "input");
            send_ajax_graph($(this).val(), date_start, date_end, "output");
        });
    }

    function send_ajax_graph(group, date_start, date_end, suffix) {
        var layout = {
            title: group + " " + suffix + " max rate",
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
        $.ajax({
            type: 'POST',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({group: group, date_start: date_start, date_end: date_end, in_out: suffix}),
            dataType: "json",

            url: "/reportes/json/interface_group_day/",
            success: function (traces) {


                var plotDiv = document.getElementById(group + "_" + suffix);
                Plotly.newPlot(plotDiv, traces, layout);


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


    function load_tables() {
        $.each(groups, function (index) {
            create_table(groups[index])

        })
    }

    function load_data() {
        var initial_date = $('#initial_date').val()
        var end_date = $('#end_date').val()
        $.each(groups, function (index) {

            send_json_request_interface(initial_date, end_date, groups[index])

        })
    }

    function create_table(group_id) {
        var table =
            '<div class="row" >\n' +

            '   <div class="col-sm-12">\n' +
            '       <table id="' + group_id + '" class="table table-bordered table-striped table-hover table-sm table-light"> \n' +
            '<h2>' + group_id + $("#initial_date").val() + " - " + $("#end_date").val() + '</h2>\n' +
            '               <input class="group_name" type="hidden" value="' + group_id + '">\n' +
            '           <thead  class="thead-dark "> ' +


            '           </thead>\n ' +
            '<tbody> </tbody>\n' +
            '       </table>\n' +
            '   </div>' +
            '   <div class="col-sm-4">\n' +
            '        <div class="row">\n' +
            '            <div class="col-sm-12">\n' +
            '               <div id="' + group_id + '_input" style="width: 100%;"></div>\n' +
            '               <div id="' + group_id + '_output" style="width: 100%;"></div>' +
            '            </div>' +
            '        </div>' +
            '   </div>' +
            '</div>'

        $('body').append(table)
    }

    function add_table_header(table_data, table_id) {
        var row_mark = $('' + table_id + ' thead').append($("<tr>"))
        $.each(column_order, function (key, value) {
            row_mark.append($("<th>").text(String(value)));
        });
    }

    function add_row_data_table(table_id, row_data) {
        var row = $('<tr>');
        $.each(column_order, function (index, key) {

            var value = row_data[key]
            var col = $('<td>');
            if (key === 'uid') {
                var a = $('<a>');
                a.text('graph');
                a.attr('href', '/interfaces/graph/' + value)
                col.append(a)
            } else {
                col.text(value);
            }

            row.append(col);

        });
        $("" + table_id + " tbody").append(row)

    }

    function create_table_json_dict(table_id, table_data) {
        $("" + table_id + " tbody").empty()
        $("" + table_id + " thead").empty()
        add_table_header(table_data, table_id);

        $.each(table_data, function (key, row) {
            add_row_data_table(table_id, row);
        })

    }

    function send_json_request_interface(initial_date, end_date, group_interfaces) {

        $.ajax({
            type: 'POST',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({
                initial_date: initial_date,
                end_date: end_date,
                group_interfaces: group_interfaces,
            }),
            dataType: "json",

            url: "/reportes/internet/json_group_interfaces",
            success: function (traces) {
                create_table_json_dict('#' + group_interfaces, traces)
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