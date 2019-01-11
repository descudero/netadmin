from __future__ import print_function

from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
from model.L3Path import L3Path
from model.claseClaro import Claro
from pprint import pprint
from multiping import multi_ping

claro = Claro()

from multiping import MultiPing

'''
# Create a MultiPing object to test three hosts / addresses
add = [
'10.10.10.2','170.80.16.1','170.80.16.3','170.80.16.7','170.80.16.9',
    '170.80.16.17','170.80.16.19','170.80.16.21','170.80.16.23','170.80.16.25',
    '170.80.16.27','170.80.16.29','170.80.16.31','170.80.16.33','170.80.16.35',
    '170.80.16.37','170.80.16.39','170.80.16.43','170.80.16.45','170.80.16.47',
    '170.80.16.49','170.80.16.51','170.80.16.53','170.80.16.55','170.80.16.59',
    '170.80.16.61','170.80.16.63','170.80.16.67','170.80.16.69','170.80.16.71',
    '170.80.16.82','170.80.16.86','170.80.16.94','170.80.16.98','170.80.16.102',
    '170.80.16.110','170.80.16.114','170.80.16.118','170.80.16.122','170.80.16.126',
    '170.80.16.134','170.80.16.138','170.80.16.142','170.80.16.146','170.80.16.150',
    '170.80.16.162','170.80.16.163','170.80.16.164','170.80.16.165','170.80.16.178',
    '170.80.16.179','170.80.16.180','170.80.16.181','170.80.16.186','170.80.16.193',
    '170.80.16.195','170.80.16.197','170.80.16.205','170.80.16.207','170.80.16.209',
    '170.80.16.215','170.80.16.217','170.80.16.225','170.80.16.230','170.80.16.233','170.80.16.235','170.80.16.238','170.80.16.250','170.80.16.253','170.80.17.66','170.80.17.74','170.80.17.78','170.80.17.90','170.80.17.98','170.80.17.102','170.80.17.110','170.80.17.114','170.80.17.118','170.80.17.122','170.80.17.142','170.80.17.170','170.80.17.174','170.80.17.193','170.80.17.195','170.80.17.197','170.80.17.214','170.80.17.218','170.80.17.221','170.80.17.235','186.148.109.72','186.148.111.9','186.148.111.170','190.61.44.6','190.106.21.174','190.107.208.2','190.107.208.3','190.107.208.4','190.107.208.5','190.107.208.7','190.107.208.11','190.107.208.12','190.107.208.19','190.107.208.21','190.107.208.28','190.107.208.29','190.107.208.36','190.107.208.41','190.107.208.44','190.107.208.45','190.107.208.54','190.107.208.55','190.107.208.67','190.107.208.68','190.107.208.69','190.107.208.75','190.107.208.82','190.107.208.85','190.107.208.91','190.107.208.92','190.107.208.110','190.107.208.114','190.107.208.115','190.107.208.116','190.107.208.118','190.107.208.120','190.107.208.123','190.107.208.124','190.107.208.171','190.107.208.174','190.107.208.177','190.107.208.182','190.107.208.186','190.107.208.194','190.107.208.195','190.107.208.196','190.107.208.203','190.107.208.204','190.107.208.205','190.107.208.211','190.107.208.218','190.107.208.219','190.107.208.226','190.107.208.244','190.107.208.247','190.107.208.250','190.107.209.2','190.107.209.4','190.107.209.22','190.107.209.26','190.107.209.34','190.107.209.38','190.107.209.42','190.107.209.54','190.107.209.58','190.107.209.62','190.107.209.66','190.107.209.70','190.107.209.78','190.107.209.82','190.107.209.99','190.107.209.114','190.107.209.122','190.107.209.138','190.107.209.162','190.107.209.163','190.107.209.165','190.107.209.166','190.107.209.167','190.107.209.168','190.107.209.169','190.107.209.170','190.107.209.171','190.107.209.172','190.107.209.173','190.107.209.174','190.107.209.175','190.107.209.176','190.107.209.178','190.107.209.179','190.107.209.180','190.107.209.181','190.107.209.182','190.107.209.183','190.107.209.184','190.107.209.185','190.107.209.186','190.107.209.187','190.107.209.188','190.107.209.189','190.107.209.190','190.107.209.211','190.107.209.212','190.107.209.214','190.107.209.226','190.107.209.228','190.107.209.229','190.107.209.234','190.107.209.235','190.107.209.236','190.107.209.237','190.107.209.238','190.107.210.2','190.107.210.6','190.107.210.10','190.107.210.18','190.107.210.26','190.107.210.98','190.107.210.99','190.107.210.100','190.107.210.101','190.107.210.102','190.107.210.104','190.107.210.105','190.107.210.107','190.107.210.109','190.107.210.122','190.107.210.123','190.107.210.124','190.107.210.125','190.107.210.126','190.107.210.130','190.107.210.162','190.107.210.166','190.107.210.170','190.107.210.174','190.107.210.186','190.107.210.190','190.107.210.198','190.107.210.202','190.107.210.217','190.107.210.219','190.107.210.230','190.107.210.235','190.107.210.237','190.107.210.241','190.107.210.246','190.107.210.250','190.107.210.254','190.107.211.13','190.107.211.66','190.107.211.74','190.107.211.195','190.107.211.196','190.107.211.197','200.9.187.34','200.9.187.35','200.9.187.36','200.9.187.39','200.9.187.40','200.9.187.44','200.9.187.47','200.9.187.50','200.9.187.51','200.9.187.52']

responses, no_responses= multi_ping(add,timeout=2,retry=10,ignore_lookup_errors=True)
# Send the pings to those addresses


# With a 1 second timout, wait for responses (may return sooner if all
# results are received).

print("responses")
print(len(responses))
print(responses)
print("no responses")
print(len(no_responses))
print(no_responses)
'''
master = Master()
test = CiscoIOS("172.17.28.192", "XR", master)
test3 = CiscoIOS("172.17.28.110", "XR", master)
test2 = CiscoIOS("172.16.30.5", "XR", master)
# test2.set_snmp_community()
# test2.set_yed_xy()
# print(test2.x)
claro.master = master

test2.hostname = 'RO-NAP-COR9K-1'
test2.platform = 'CiscoXR'

test2.set_interfaces()

# test2.set_interfaces()

# interfaces = [interface for interface in test2.interfaces.values()
#              if interface.l3_protocol == "BGP" and
#             interface.l3_protocol_attr == "IPT"
#              ]

# for interface in interfaces:
#    interface.save_state()
# test2.set_interfaces()

# interfaces=[interface for index,interface in test2.interfaces.items() if interface.l3_protocol=="BGP"]
# pprint(interfaces)
# pprint(claro.get_service_instance_with_pseudowires([test, test3]))
# devices =claro.devices_from_network("172.16.30.128/25")
# pprint(devices)

# test.set_snmp_community()
# test.set_snmp_plattform()
# claro.ospf_topology(ip_seed_router='172.16.30.5', process_id='1', area='0')
# print(test.set_arp_list(vrf="INTERNET"))


# pprint(test.get_vfis_interface_per_service_instance())
# test2.set_chassis()
# print(test2.chassis)
# test2.chassis.print_children()

# pprint(test2.get_ospf_area_adjacency_p2p())

# pprint(test2.set_physical_interfaces())
# devices = claro.load_devices_csv("host.csv")
# claro.asr_mod_inventory()
# for device in devices:
#    pprint(device.set_inventory())

# test2.set_jump_gateway("10.250.55.3","telnet")
# arp_list =test2.set_arp_list()
# pprint(arp_list)
# claro.save_to_excel_dict(arp_list,'arp_edge2')


# responses,no_responses = test2.internet_validation_arp("prueba_ping",vrf="default")
# print(test.print_bgp_advertise(bgp_neigbor_ip="2001:688:0:2:7::59",address_family="vrf INTERNET ipv6 unicast"))
# print(test.print_bgp_advertise(bgp_neigbor_ip="2001:41a8:4020:2::10d ",address_family="vrf INTERNET ipv6 unicast"))

# interfaz="Gi2/3"

# test.set_interfaces_stats(interfaces_index=[interfaz])
# print(test.interfaces[interfaz].get_interface_summary())
# show_route=IpRoute.get_show_ip_route(connection=test.connect(),parent_device=test,prefix="10.1.51.28")
# print(show_route)
# route=IpRoute.parse_route_xr(show_route)
# claro.set_master(password="zekto2014-",username="descudero")
# claro.ospf_save_adj()
# claro.opsf_check_mtu_adjacencies()
# claro.ospf_save_excel_adj()
# claro.consulted_devices()
# claro.search_ipt_prefix_advertisement(prefix_list=["152.231.168.0/22"],address_family="vrf INTERNET ipv4 unicast")
# pprint(test.get_bgp_neighbor_advertised_routes(bgp_neigbor_ip="2001:2000:3080:ae9::1 ",address_family=" vrf INTERNET ipv6 unicast "))


# print(test.print_bgp_neighbors(address_family="vrf INTERNET"))
# claro.search_recived_routers_ipt_advertise("10.244.1.12","ESC","CUS",address_family="vrf INTERNET ipv4 unicast")

# test2.set_ip_ospf_interfaces()
# interfaces_index = test2.ospf_interfaces.keys()
# test2.set_interfaces_stats(interfaces_index=interfaces_index)

# l3test = L3Path(claro,"10.192.33.7","10.192.129.13",vrf="null")
# l3test.search_recursive_path_route()
# print(l3test.string_path())
# print(l3test.get_interfaces_stats())
# l3test.get_log(filter=" Mar 12")

# claro.set_master(username="descudero",password="zekto2014-")

# print(claro.check_device_up(test))
# print(claro.adj_report("prueba_final_con_check_60_equipos_final2","listado.csv"))
# claro.get_rows_sql_report("prueba_daniel2")
# claro.ospf_save_adj()
# test = CiscoIOS("10.192.33.7","ios",master)
# print(test.get_ip_ospf_processes())
# test2 = CiscoXR("10.192.0.241","ios",master)
# print(test2.save_ospf_adjacencies())
# connection = test.connect()
# output= test2.set_mpls_ldp_interface()
# test2.save_report_sql("mpls_ldp_interfaces")
# output2 = test.set_ip_ospf_interface()
# test2.set_pim_interfaces()4
# test2.save_report_sql("pim_interfaces")
# print(output)
# print(output2)


# test2 = CiscoIOS("192.168.205.55","XR",master)

# test2.set_jump_gateway("10.250.55.3","telnet")
# print(test2.create_policies_bgp_neighbors(address_family="ipv6 unicast"))

# print(test2.create_policies_bgp_neighbors(address_family="ipv4 unicast"))
