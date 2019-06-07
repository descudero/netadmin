import copy


class IpExplicitPath:
    def __init__(self, name, hops, parent_device):
        self.hops = hops
        self.name = name
        self.parent_device = parent_device

    def ips_on_path(self, ips, mode='all'):
        data = [self.ip_on_path(ip=ip) for ip in ips]
        if mode == 'all':
            return all(data)
        elif mode == 'any':
            return any(data)
        elif mode == 'one':
            return len([dat for dat in data if dat]) == 1

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

    def del_hops_between(self, hop1, hop2):
        index_a = int(self.index_of_ip(ip=hop1))
        index_b = int(self.index_of_ip(ip=hop2))

        index_a, index_b = index_a, index_b if index_a < index_b else index_b, index_a

        for index in range(index_a + 1, index_b):
            self.hops.pop(str(index), None)




    def copy_path_new_hop(self, ip_reference_hop, hop, index_way="before", suffix="_NEW"):

        new_path = copy.copy(self)
        new_path.hops = copy.deepcopy(self.hops)
        new_path.name = new_path.name + suffix
        new_path.add_hop(new_path.index_of_ip(ip=ip_reference_hop), hop=hop, index_way=index_way)

        return new_path

    @property
    def command(self):
        command_string = f"explicit-path name  {self.name}  enable\n"
        if self.parent_device.platform == "CiscoIOS":
            command_string = f'ip {command_string}'
        for index, hop in enumerate(self):
            if self.parent_device.platform == "CiscoXR":
                command_string += f"index {(index + 1) * 7}  "
            command_string += f" next-address {hop['loose']}  {hop['next_hop']} \n"

        return command_string

    def __iter__(self):
        return iter(self.hops)

    def __repr__(self):
        data = f"{self.name} " + "|".join([hop["next_hop"] for hop in self])
        return data
