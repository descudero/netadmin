from collections import OrderedDict


class MplsTeTunnel:
    def __init__(self, txtfsmdata, parent):
        self.parent = parent
        for attr, value in txtfsmdata.items():
            setattr(self, attr, value)
        self.paths = OrderedDict()
        for path in self.path_option:
            index = path.split(",")[0]
            path_data = path.split(",")[1].replace("type", " ")
            if "dynamic" in path_data:
                type_path = "dynamic"
                name = ""
            else:
                name = path_data.split("explicit")[1].replace(" ", "")
                type_path = "explicit"
            self.paths[index] = {"index": index, "path_type": type_path, "name": name}

    def get_new_index_path(self, index, index_way="after"):
        index = int(index)
        while str(index) in self.paths:
            if index_way == "after":
                index += 1
            else:
                index -= 1
            if index > 1:
                return None
        return str(index)

    def add_hop_ip_explicit_paths(self, hop, ip_reference_hop, index_way_path="before", index_way_tunnel=""):
        new_paths = {}

        for index, path in self.paths.items():

            if path["path_type"] == "explicit":

                if self.parent.explicit_paths[path["name"]].ip_on_path(ip=ip_reference_hop):
                    explicit_path = self.parent.explicit_paths[path["name"]]
                    new_paths[index] = explicit_path.copy_path_new_hop(
                        ip_reference_hop=ip_reference_hop, hop=hop, index_way=index_way_path)
        command_path = ""
        comand_tunnel = " interface tunnel " + self.tunnel + "\n"
        for index, path in new_paths.items():
            command_path += path.command
            comand_tunnel += self.add_explicit_path(index, name=path.name, index_way=index_way_tunnel)
        return command_path + comand_tunnel

    def add_explicit_path(self, index, name, index_way="after"):
        index = self.get_new_index_path(index, index_way=index_way)
        if index is not None:
            return " tunnel mpls traffic-eng path-option " + index + " explicit " + name + "\n"
        else:
            return ""
