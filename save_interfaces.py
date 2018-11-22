from model.CiscoIOS import CiscoIOS
from model.claseClaro import Claro
from config.Master import Master
from model.CiscoXR import CiscoXR
from pprint import pprint

claro = Claro()
master = Master(password="zekto2014-", username="descuderor")
# test = CiscoXR("172.16.30.244","XR",master)
claro.set_master(password="zekto2014-", username="descuderor")

# print(test.set_arp_list(vrf="INTERNET"))
test2 = CiscoXR("10.235.252.18", "IOS", master)
# test2.set_chassis()
# print(test2.chassis)
# test2.chassis.print_children()

pprint(claro.generate_report_consumption(network="172.16.30.0/24", filename="interfaces_regionales"))
# test2.set_all_interfaces()
# pprint(test2.interfaces)
