from os import listdir
import re
import copy


class ConfigTemplate:
    def __init__(self, template_name):
        pattern = re.compile("\$((\d|\w|_)*)")
        template_name = 'resources/config_template/' + template_name
        template_name = template_name if ".template" in template_name else template_name + ".template"
        with open(template_name, "r") as template:
            self.template = template.read()
            self.fields = [data[0] for data in list(set(pattern.findall(self.template)))]
            self.fields.sort(key=len, reverse=True)

    def render(self, values=dict) -> str:
        text = copy.copy(self.template)
        for field in self.fields:
            text = text.replace("$" + field, values.get(field, "<h4>NO_DATA_FOR_FIELD" + field + "</h4>"))
        return text

    def render_html(self, values=dict) -> str:
        text = copy.copy(self.template)
        for field in self.fields:
            text = text.replace("$" + field, values.get(field, "<h4>NO_DATA_FOR_FIELD" + field + "</h4> "))
        return text.replace('\n', '<br/>')

    def get_json_fields(self):
        pass

    @staticmethod
    def get_all_templates_names():
        return list(listdir("./resources/config_template/"))
