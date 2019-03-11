from collections import OrderedDict
from tools import logged


@logged
class MplsTeTunnel:
    def __init__(self, txtfsmdata, parent):
        self.parent = parent
        for attr, value in txtfsmdata.items():
            setattr(self, attr, value)
        self.paths = OrderedDict()
        if hasattr(self, "path_option"):
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
        self.protected_paths = {}
        if hasattr(self, "path_protected_option"):
            for path in self.paths_protected_option:
                index = path.split(",")[0]
                path_data = path.split(",")[1].replace("type", " ")
                if "dynamic" in path_data:
                    type_path = "dynamic"
                    name = ""
                else:
                    name = path_data.split("explicit")[1].replace(" ", "")
                    type_path = "explicit"
                self.protected_paths[index] = {"index": index, "path_type": type_path, "name": name}

        self.indexes = list(self.paths.keys())

        self.indexes_protected = list(self.protected_paths.keys())

    def get_new_index_protected_path(self, index, index_way="after"):
        index = int(index)
        while str(index) in self.indexes:
            if index_way == "after":
                index += 1
            else:
                index -= 1
            if index < 1:
                return self.get_new_index_protected_path(index=index, index_way="after")
        return str(index)

    def get_new_index_path(self, index, index_way="after"):
        index = int(index)
        while str(index) in self.indexes:
            if index_way == "after":
                index += 1
            else:
                index -= 1
            if index < 1:
                return self.get_new_index_path(index=index, index_way="after")
        return str(index)

    def add_hop_ip_explicit_paths(self, hop, ip_reference_hop, index_way_path="before", index_way_tunnel="",
                                  suffix_path="NEW"):
        new_paths = {}
        new_protected_paths = {}
        command_path = ""
        comand_tunnel = ""
        for index, path in self.paths.items():

            if path["path_type"] == "explicit":
                try:
                    if self.parent.explicit_paths[path["name"]].ip_on_path(ip=ip_reference_hop):
                        comand_tunnel += " interface tunnel " + self.tunnel + "\n"
                        explicit_path = self.parent.explicit_paths[path["name"]]
                        new_paths[index] = explicit_path.copy_path_new_hop(
                            ip_reference_hop=ip_reference_hop, hop=hop, index_way=index_way_path, suffix=suffix_path)
                        comand_tunnel += self.add_explicit_path(index, name=new_paths[index].name,
                                                                index_way=index_way_tunnel)
                        self.parent.explicit_paths[new_paths[index].name] = new_paths[index]
                except KeyError as e:
                    self.verbose.warning(
                        "add_hop_ip_explicit_paths dev{0} no P {1}".format(self.parent.ip, path["name"]))
        self.paths = {**self.paths, **{
            index: {"index": index, "path_type": "explicit", "name": path.name} for index, path in new_paths.items()}}
        self.indexes = list(self.paths.keys())

        for index, path in new_paths.items():
            command_path += path.command

        return command_path + comand_tunnel

    def add_explicit_path(self, index, name, index_way="after"):
        index = self.get_new_index_path(index, index_way=index_way)
        if index is not None:
            self.indexes.append(index)
            return " tunnel mpls traffic-eng path-option " + index + " explicit name " + name + "\n"
        else:
            return ""

    def complete_mid_point_te(self, device):
        try:
            return device.mpls_te_tunnels[self.tunnel]
        except KeyError as e:
            self.verbose.warning(
                "complete_mid_point_te key error TI {0} SIP {1} Tunnels {2}".format(self.tunnel,
                                                                                    self.source_ip,
                                                                                    len(device.mpls_te_tunnels)))
        except AttributeError as e:
            self.verbose.warning("complete_mid_point_te attr TI {0} SIP {1} dev {2}".format(self.tunnel,
                                                                                            self.source_ip,
                                                                                            device.__class__.__name__))
            return None
