from __future__ import print_function

from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
from model.L3Path import L3Path
from model.claseClaro import Claro
from pprint import pprint
from multiping import multi_ping
from collections import Counter

claro = Claro()

final_counter = Counter()
master = Master()
test = CiscoIOS("10.242.55.5", "XR", master)
test.set_jump_gateway("10.250.55.3", protocol="telnet")
# test3 = CiscoIOS("172.17.28.110", "XR", master)
# test2 = CiscoXR("172.16.30.253", "XR", master)

# test2.set_snmp_community()
# test2.set_yed_xy()
# print(test2.x)
claro.master = master
# xrs = CiscoXR.devices(master)

test.create_file_nagios_arp()

# devices = CiscoXR.devices(master)
# pprint(devices)
'''
devices,ips = claro.devices_from_network("172.16.30.0/24")

claro.excute_methods(methods={"set_snmp_location":{}},devices=devices)

pprint(len(devices))
data = [{"ip":device.ip,"hostname":device.hostname, "snmp_location":device.snmp_location} for device in devices]

claro.save_to_excel_list(data,file_name="snmp_location")
'''
