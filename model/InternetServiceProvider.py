from os import listdir
from model.claseClaro import Claro
from os.path import isfile, join
import time
from model.CiscoIOS import CiscoIOS


class InternetServiceProvider(Claro):

    @staticmethod
    def search_file_name(folder, match):
        files = [file for file in listdir(folder) if match in file]

        return files

    def ospf_topology_dict_vs_date(self, name="ospf_ufinet_regional", date_string=time.strftime("%Y%m%d")):
        date_string = date_string.replace("-", "")
        files = InternetServiceProvider.search_file_name("shelves", date_string)
        if files:
            result = super().ospf_topology_vs(ip_seed_router="172.16.30.5",
                                              shelve_name="shelves/" + date_string + "_" + name, from_shelve=True)
        else:
            result = super().ospf_topology_vs(ip_seed_router="172.16.30.5",
                                              shelve_name="shelves/" + date_string + "_" + name,
                                              from_shelve=False)

        return result

    def get_mpls_te_end_points(self, devices=[]) -> list:
        devices_set = set(devices)
        devices = self.correct_device_platform(self.devices_from_ip_list(devices))
        self.excute_methods(methods={"set_mpls_te_tunnels_mid_point": {}, "set_mpls_te_tunnels": {}}, devices=devices)
        for device in devices:
            devices_set = devices_set | device.get_te_head_ip_set()
            print(devices_set)
            print(len(devices_set))
        devices = self.correct_device_platform(self.devices_from_ip_list(devices_set))
        return devices

    def replace_loose_mpls_te_paths(self, abr_ip, new_abr_ip, devices=[],
                                    suffix_path="NEW"):
        devices = self.get_mpls_te_end_points(devices=devices)
        self.excute_methods(methods={"set_mpls_te_tunnels": {}, "set_ip_explicit_paths": {}}, devices=devices)
        devices = sorted(devices, key=lambda o: o.ip)

        print([device.ip for device in devices])
        final_command = f"\n---------------------------------------------\ntotal devices {len(devices)} \n"

        for index, device in enumerate(devices):
            command = device.head_te_add_hop_ip_explicit_paths(hop={"next_hop": new_abr_ip, "loose": "loose"},
                                                               ip_reference_hop=abr_ip,
                                                               index_way_path="replace", index_way_tunnel="before",
                                                               suffix_path=suffix_path)
            if command != "":
                final_command += f" no {index} next_device {device.ip} \n {command}"

        return final_command

    def add_interface_mpls_te_paths(self, ip_a: str, ip_b: str, ip_a_new_hop: dict, ip_b_new_hop: dict, devices=[],
                                    suffix_path="NEW"):
        devices = self.get_mpls_te_end_points(devices=devices)

        self.excute_methods(methods={"set_mpls_te_tunnels": {}, "set_ip_explicit_paths": {}}, devices=devices)
        devices = sorted(devices, key=lambda o: o.ip)

        final_command = ""

        for device in devices:
            command = device.head_te_add_hop_ip_explicit_paths(hop=ip_b_new_hop, ip_reference_hop=ip_b,
                                                               index_way_path="before", index_way_tunnel="before",
                                                               suffix_path=suffix_path)
            command += device.head_te_add_hop_ip_explicit_paths(hop=ip_a_new_hop, ip_reference_hop=ip_a,
                                                                index_way_path="after", index_way_tunnel="before",
                                                                suffix_path=suffix_path)
            if command != "":
                final_command += device.ip + "\n" + command

        return final_command
