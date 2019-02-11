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

    def add_new_paths_mpls_te(self, ip_a, ip_b, ip_a_new_hop, ip_b_new_hop, ip_source_device, suffix_path="NEW"):
        initial_device = CiscoIOS(ip=ip_source_device, master=self.master, display_name=ip_source_device)
        initial_device.ip_explicit_paths()
        initial_device.set_mpls_te_tunnels()
        initial_device.set_mpls_te_tunnels_mid_point()
        devices = initial_device.complete_mpls_te_mid_point_source_device(isp=self)
        devices.append(initial_device)
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
