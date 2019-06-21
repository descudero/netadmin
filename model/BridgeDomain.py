from tools import normalize_interface_name
from model.InterfaceUfinet import InterfaceUfinet

class BridgeDomain:

    def __init__(self, id_bd, parent_device):
        self.parent_device = parent_device
        self.id_bd = id_bd
        self.interfaces = {}
        self.vfis = {}
        self.routed_interface = f"BDI{id_bd}"

    def add_interfaces(self, interface_data):
        '''
        Value interface_name (\S+)
        Value service_instance (\d+)
        '''
        index = InterfaceUfinet.get_normalize_interface_name(interface_data["interface_name"])
        if index != '':
            if "BDI" in index:
                self.routed_interface = index
            else:
                self.interfaces[index] = interface_data

    def add_vfi(self, vfi_data):
        '''
                Value Filldown bride_domain (\d+)
                Value interface_name (\S+)
                Value neighbor_ip ((\d{1,3}\.){3}\d{1,3})
                Value vfi_vc_id (\d+)

                :return:
                '''
        index = InterfaceUfinet.get_normalize_interface_name(vfi_data["interface_name"])
        if index != '':
            if index not in self.vfis:
                self.vfis[index] = [vfi_data]
            else:
                self.vfis[index].append(vfi_data)

    def __repr__(self):
        return str(self.__class__) + " id " \
               + self.id_bd + " vfi " + str(len(self.vfis)) \
               + " int " + str(len(self.interfaces))

    def get_string_vfi(self):
        output = ""
        for key, vfis in self.vfis.items():
            output += " ".join(["vfi:", key, "\n"])
            for vfi in vfis:
                output += " ".join(["nei:", vfi["neighbor_ip"], 'vcid', vfi["vfi_vc_id"], '\n'])

        return output

    def interface_bridge_domain(self, interface, service_instance):
        if interface in self.interfaces:
            return self.interfaces[interface]['service_instance'] == service_instance
        return False

    def get_first_interface(self):
        for index, interface in self.interfaces.items():
            return index, interface['service_instance']
