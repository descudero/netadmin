$(document).ready(function () {
    console.log("document ready");

    date_start = $("#initial_date").val();
    date_end = $("#end_date").val();
    $(".group_name").each(function () {
        console.log($(this).val())
        send_ajax_graph($(this).val(), date_start, date_end, "input");
        send_ajax_graph($(this).val(), date_start, date_end, "output");
    });

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
                Plotly.plot(plotDiv, traces, layout);


                console.log("en teoria terminamos algo");
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

