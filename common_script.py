from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
import time

isp = ISP()
isp.master = Master()

# print(isp.ospf_topology_vs(ip_seed_router="172.16.30.5"))
'''
with open("loose_vpl.txt", "w") as f:
    data = isp.replace_loose_mpls_te_paths(abr_ip="172.16.30.44", new_abr_ip="172.16.30.251",
                                           devices=["172.16.30.44", "172.16.30.45"],
                                           suffix_path="_MIG_CER_VPL")

    f.write(data)'''
data = [{
    "ip_a": "172.16.20.65", 'ip_b': "172.16.20.66",
    'ip_a_new_hop': {"next_hop": "172.16.20.129", "loose": ""},
    'ip_b_new_hop': {"next_hop": "172.16.20.130", "loose": ""}
},
    {
        "ip_a": "172.16.20.86", 'ip_b': "172.16.20.87",
        'ip_a_new_hop': {"next_hop": "172.16.20.129", "loose": ""},
        'ip_b_new_hop': {"next_hop": "172.16.20.130", "loose": ""}
        , 'devices': ["172.16.30.1"], 'suffix_path': "_MIG_CMYs"
    }
    ,
    {
        "ip_a": "172.16.20.58", 'ip_b': "172.16.20.57",
        'ip_a_new_hop': {"next_hop": "172.16.20.129", "loose": ""},
        'ip_b_new_hop': {"next_hop": "172.16.20.130", "loose": ""}
        , 'devices': ["172.16.30.1"], 'suffix_path': "_MIG_CMYs"
    }
    ,
    {
        "ip_a": "172.16.20.73", 'ip_b': "172.16.20.74",
        'ip_a_new_hop': {"next_hop": "172.16.20.137", "loose": ""},
        'ip_b_new_hop': {"next_hop": "172.16.20.138", "loose": ""}
        , 'devices': ["172.16.30.5"], 'suffix_path': "_MIG_CMYs"
    }
    ,
    {
        "ip_a": "172.16.20.9", 'ip_b': "172.16.20.10",
        'ip_a_new_hop': {"next_hop": "172.16.20.157", "loose": ""},
        'ip_b_new_hop': {"next_hop": "172.16.20.158", "loose": ""}
        , 'devices': ["172.16.30.5"], 'suffix_path': "_MIG_CMYs"
    }
    ,
    {
        "ip_a": "172.16.20.106", 'ip_b': "172.16.20.105",
        'ip_a_new_hop': {"next_hop": "172.16.20.157", "loose": ""},
        'ip_b_new_hop': {"next_hop": "172.16.20.158", "loose": ""}
        , 'devices': ["172.16.30.5"], 'suffix_path': "_MIG_CMYs"
    }

    ,
    {
        "ip_a": "172.16.20.173", 'ip_b': "172.16.20.174",
        'ip_a_new_hop': {"next_hop": "172.16.20.157", "loose": ""},
        'ip_b_new_hop': {"next_hop": "172.16.20.158", "loose": ""}
        , 'devices': ["172.16.30.5"], 'suffix_path': "_MIG_CMYs"
    }
]

result_final = "***************************\n*********************\n" + \
               isp.add_interface_mpls_te_paths(hops_data=data, devices=["172.16.30.1", "172.16.30.5"],
                                               suffix_path="_MNP")

with open("migracion_cmy.txt", "w") as f:
    f.write(result_final)
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
