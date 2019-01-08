$(document).ready(function () {

    console.log("logramos algo")
    $.ajax({
        dataType: "json",
        url: "/reportes/json",
        success: function (traces) {
            console.log("logramos algo");

            var plotDiv = document.getElementById('myDiv');
            for (trace in traces) {
                console.log(traces[trace])
                Plotly.newPlot(plotDiv, traces[trace], {title: 'stacked and filled line chart'});
            }


            console.log("en teoria terminamos algo");
        },
        error: function (xhr, ajaxOptions, thrownError) {
            alert(xhr.status);
            alert(thrownError);
        },
        complete: function () {
            // Handle the complete event
            alert("ajax completed ");
        }
    });


});