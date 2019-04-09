from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
import time

isp = ISP()
isp.master = Master()
device_list = ["172.16.30.128"]
network = "172.16.30.0/24"

devices = isp.devices_from_ip_list(device_list)
isp.excute_methods(methods={"set_snmp_community": {}}, devices=devices)
isp.excute_methods(methods={"set_snmp_location_attr": {}, "set_interfaces": {}}, devices=devices)

data_dict = [{"0_ip": device.ip, "1_hostname": device.hostname, "2_country": device.country, "3_index": index,
              "4_description": interface.description}
             for device in devices
             for index, interface in device.interfaces.items() if
             "Te" in index and not "." in index and not "L3:" in interface.description]

output = ""

for device in devices:
    output += f"\n-------------------------------\n ip {device.ip} hostname {device.hostname}" \
        f"\n-------------------------------\n"
    for if_index, interface in device.interfaces.items():
        if "Te" in if_index and not "." in if_index and not "L3:" in interface.description:
            output += f"interface {if_index})\n "
            output += f" description L3:MPLOSP D:B L1:DP {interface.description}\n"

with open("regional.txt", "w") as file:
    file.write(output)
isp.save_to_excel_list(data_dict, "regional interfaces")
'''
cisco.set_mpls_te_tunnels()
cisco.set_mpls_te_tunnels_mid_point()
cisco.complete_mpls_te_mid_point_source_device(isp)
none = [0 for tunnel in cisco.mpls_te_tunnels_mid_point.values() if tunnel is None]
print(len(cisco.mpls_te_tunnels_mid_point.items()))
print("none ",len(none))
'''
'''cisco2 = CiscoXR(ip="172.16.30.248", display_name="", master=isp.master)
cisco2.set_interfaces()

isp.save_to_excel_list(list_data=[interface.dict_data()
                                  for interface in cisco2.interfaces.values()
                                  if "." not in interface.if_index
                                  and interface.util_in < 2
                                  and interface.util_out < 2 and
                                  "Te" in interface.if_index]
                       , file_name="interfaces_fisicas" + cisco2.ip)'''
'''
cisco.set_mpls_te_tunnels()
print(cisco.mpls_te_tunnels)
cisco.ip_explicit_paths()
for index, tunnel in cisco.mpls_te_tunnels.items():
    print(tunnel.add_hop_ip_explicit_paths(ip_reference_hop="172.16.20.85",
                                           hop={"next_hop": "1.1.1.1", "loose": ""},
                                           index_way_path="before", index_way_tunnel="after"))
'''
# new_paths=cisco.add_hop_ip_explicit_paths(ip_reference_hop="172.16.25.14",hop={"next_hop":"1.1.1.1","loose":""},index_way="replace")


'''
cisco = CiscoXR(ip="172.16.30.254", display_name="", master=isp.master)

cisco.set_snmp_location_attr()
print(cisco.country)
devices = CiscoXR.devices(isp.master)
isp.do_uni_methods(devices=devices, methods={"set_snmp_location_attr":{}})
for device in devices:
    print(device.ip)
    print(device.country)
'''
