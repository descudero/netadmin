import copy


class IpExplicitPath:
    def __init__(self, name, hops, parent_device):
        self.hops = hops
        self.name = name
        self.parent_device = parent_device

    def index_of_ip(self, ip):
        for index, hop in enumerate(self):
            if hop["next_hop"] == ip:
                return index
        else:
            return -1

    def ip_on_path(self, ip):
        return self.index_of_ip(ip=ip) >= 0

    def add_hop(self, index, hop, index_way="before"):
        if index_way == "before":
            self.hops.insert(index, hop)
        elif index_way == "after":
            self.hops.insert(index + 1, hop)
        elif index_way == "replace":
            self.hops[index] = hop

    def copy_path_new_hop(self, ip_reference_hop, hop, index_way="before", suffix="_NEW"):

        new_path = copy.copy(self)
        new_path.hops = copy.deepcopy(self.hops)
        new_path.name = new_path.name + suffix
        new_path.add_hop(new_path.index_of_ip(ip=ip_reference_hop), hop=hop, index_way=index_way)

        return new_path

    @property
    def command(self):
        command_string = f" ip explicit-path name  {self.name}  enable\n"
        for hop in self:
            command_string += f" next-address {hop['loose']}  {hop['next_hop']} \n"

        return command_string

    def __iter__(self):
        return iter(self.hops)

    def __repr__(self):
        data = f"{self.name} " + "|".join([hop["next_hop"] for hop in self])
        return data
