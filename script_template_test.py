from support.ConfigTemplate import ConfigTemplate

template = ConfigTemplate("mpls_device_xr")
text = template.render({"$interface_index": "Ten0/3/3"})
print(template.fields)

print(ConfigTemplate.get_all_templates_names())
