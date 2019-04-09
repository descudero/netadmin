$(document).ready(function () {
        var global_fields = []
        $('#loading_json').hide()
        var device_type = $('#device_type').val()
        get_config_templates(device_type)

        $('#device_type').change(function (event) {
            var device_type = $('#device_type').val()
            get_config_templates(device_type)
            var template_name = $("#config_template").val()
            get_template_fields(template_name)


        });

        $('#config_template').change(function (event) {
            var template_name = $("#config_template").val()
            get_template_fields(template_name)

        });

        $('#request_fields').click(function (e) {
            var template_name = $("#config_template").val()
            get_template_fields(template_name)

        });

        $('#render_config_template').click(function (e) {
            var form_data = Object()
            var template_name = $("#config_template").val()
            $.each(global_fields, function (index, field) {
                form_data[field] = ($("#" + field).val())
            })

            console.log(form_data)
            render_config_template(template_name, form_data)

        });

        function render_config_template(template_name, form_data) {
            $.ajax({
                type: 'POST',
                contentType: 'application/json;charset=UTF-8',
                data: JSON.stringify({template_name: template_name, form_data: form_data}),
                dataType: "json",

                url: "/utilidades/render_config_template",
                success: function (config) {
                    $("#config").empty()
                    $("#config").html(config['config'])
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

        function get_config_templates(device_type) {
            $.ajax({
                type: 'POST',
                contentType: 'application/json;charset=UTF-8',
                data: JSON.stringify({device_type: device_type}),
                dataType: "json",

                url: "/utilidades/plantillas_disponibles",
                success: function (templates) {
                    add_templates(templates)
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

        function add_form_field(field, form) {
            var div = '<div class="form-group row"> <label for="' + field + '" class="col-sm-4 col-form-label col-form-label-lg">' + field + '</label> <div class="col-sm-8"> <input type="text" class="template_field form-control form-control-lg" id="' + field + '" placeholder="' + field + ' name="' + field + '" > </div> </div>'
            form.append(div)
        }

        function add_templates(templates) {
            $('#config_template').empty()
            var options = $('#config_template').attr('options');
            console.log(options)
            console.log(templates)
            $.each(templates, function (key, value) {
                $("#config_template").append(new Option(value, value));
            });

        }


        function create_form_template(fields, form_name) {
            $("#config").empty()
            global_fields = fields
            var form = $(form_name)
            form.empty()
            $.each(fields, function (index, field) {
                add_form_field(field, form)

            });

        }


        function get_template_fields(template_name) {
            ;
            $.ajax({
                type: 'POST',
                contentType: 'application/json;charset=UTF-8',
                data: JSON.stringify({template_name: template_name}),
                dataType: "json",

                url: "/utilidades/template_fields",
                success: function (fields) {
                    create_form_template(fields, "#template_form")

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

    }
);