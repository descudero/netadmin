from model.claseClaro import Claro
from config.Master import Master
from model.CiscoIOS import CiscoIOS

file = open("mpls_te.txt")
show_output = file.read()

claro = Claro()
claro.set_master(username="descuderor", password="zekto2014-")
# claro.tabulate_mpls_traffic_tunnels(show_output)
master = Master(username="descuderor", password="zekto2014-")
test2 = CiscoIOS("172.19.28.21", "IOS", master)
# test2.set_pseudo_wire_class()
# print(test2.get_pw_class_by_tunnel_if("50620"))
# test2.set_pseudowires()
# test2.set_service_instances()
# print(test2.get_service_instance_by_tunnel_id("50507"))
# test2.set_mpls_te_tunnels()
claro.tabulate_mpls_traffic_tunnels("172.16.30.4")
'''
test2.set_template_type_pseudowires()
test2.set_vfis()
test2.set_bridge_domains()
test2.set_service_instances()
template = (test2.get_template_by_tunnel_id("5657"))
vfi = test2.get_vfi_by_template(template)
interfaces = test2.get_interfaces_instance_by_vfi(vfi)
service_instance = test2.get_service_instance_by_interfaces(interfaces)
print(service_instance)
'''
