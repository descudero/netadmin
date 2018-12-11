from __future__ import print_function

from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
from model.L3Path import L3Path
from model.claseClaro import Claro
from pprint import pprint

claro = Claro()
master = Master(password=Master.decode("ufinet", "w4rDjMOSw5zDisOowqbCnsOI"),
                username=Master.decode("pinf con vrf", "w5fDjsOhw5rCicOSw50="))
# test = CiscoXR("10.234.5.171","XR",master)
# test_ios = CiscoIOS("10.243.1.8","IOS",master)
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


# print(test.create_policies_bgp_neighbors(address_family=" vrf INTERNET "))
# print(test_ios.create_policies_bgp_neighbors(address_family="ipv6 unicast",country_key="SV"))
# search_recived_routers_ipt_advertise

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
