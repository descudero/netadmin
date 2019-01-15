from __future__ import print_function

from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
from model.L3Path import L3Path
from model.claseClaro import Claro
from pprint import pprint
from multiping import multi_ping

claro = Claro()

master = Master()
test = CiscoIOS("172.17.28.192", "XR", master)
test3 = CiscoIOS("172.17.28.110", "XR", master)
test2 = CiscoXR("172.16.30.244", "XR", master)
# test2.set_snmp_community()
# test2.set_yed_xy()
# print(test2.x)
claro.master = master

claro.ospf_topology("172.16.30.5", filename="ospf_regional")

'''
devices,ips = claro.devices_from_network("172.16.30.0/24")

claro.excute_methods(methods={"set_snmp_location":{}},devices=devices)

pprint(len(devices))
data = [{"ip":device.ip,"hostname":device.hostname, "snmp_location":device.snmp_location} for device in devices]

claro.save_to_excel_list(data,file_name="snmp_location")
'''
