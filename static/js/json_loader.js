$(document).ready(function () {
    $.ajax({
        dataType: "json",
        url: "/internet/isp/total/json",
        data: data,
        success: function (data) {
            for (var graph_name in json_data) {
                var graph_data = json_data[graph_name]
                var y1_data = {
                    name: graph_name, stackgroup: "y1", x: graph_data["x"],
                }
                var plotDiv = document.getElementById('plot');

                Plotly.newPlot(plotDiv, traces, {title: 'Normalized stacked and filled line chart'});

            }

        }
    });
});

