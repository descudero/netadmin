from functools import cmp_to_key


class CiscoPart(object):
    def __init__(self, parent_device, name, serial_number, vid, pid, local_name):
        self.parent_device = parent_device
        self.name = name
        self.serial_number = serial_number
        self.vid = vid
        self.pid = pid
        self.local_name = local_name
        self.part_level = local_name.count("/")
        self.children = {}

    def print_children(self, recursive=True):
        for id, child in self.children.items():
            print("\t" * self.part_level + str(child))
            if recursive:
                child.print_children(recursive)

    def is_parent(self, part):
        if self.part_level == part.part_level - 1 and self.is_related(part):
            return True
        return False

    def add_child(self, part):
        if (self.is_parent(part)):
            part.parent = self
            self.children[part.local_name] = part
            return True
        else:
            return_value = False
            for name, child in self.children.items():

                if (child.is_related(part)):
                    return_value = child.add_child(part)
            return return_value

    def is_related(self, children):

        if children.local_name.startswith(self.local_name):
            return True
        else:
            return False

    @staticmethod
    def create_inventory_tree(device, inventory):
        device.inventory_tree = {}
        parts = []
        for inventory_part in inventory:
            part = CiscoPart(
                parent_device=device,
                name=inventory_part["description"],
                serial_number=inventory_part["SN"],
                vid=inventory_part["VID"],
                pid=inventory_part["PID"],
                local_name=inventory_part["local_name"])
            parts.append(part)

        parts.sort(key=lambda x: x.part_level, reverse=False)

        while len(parts) != 0:
            part = parts.pop()
            if (part.part_level == 1):
                device.inventory_tree[part.local_name] = part

            else:
                added_in_tree = False
                keys = [*device.inventory_tree]
                while not added_in_tree and len(keys) != 0:
                    level_1_part = device.inventory_tree[keys.pop()]
                    added_in_tree = level_1_part.add_child(part)

                if (not added_in_tree):
                    parts.insert(0, part)

    def __str__(self):
        return self.local_name + " " + self.pid
