from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
import time

isp = ISP()
isp.master = Master()

# print(isp.ospf_topology_vs(ip_seed_router="172.16.30.5"))

cisco = CiscoIOS(ip="172.16.30.5", display_name="", master=isp.master)

cisco.set_mpls_te_tunnels()
print(cisco.mpls_te_tunnels)
cisco.ip_explicit_paths()
for index, tunnel in cisco.mpls_te_tunnels.items():
    print(tunnel.add_hop_ip_explicit_paths(ip_reference_hop="172.16.20.85",
                                           hop={"next_hop": "1.1.1.1", "loose": ""},
                                           index_way_path="before", index_way_tunnel="after"))

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
