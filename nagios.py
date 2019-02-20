from __future__ import print_function

from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.claseClaro import Claro
from collections import Counter
import argparse

parser = argparse.ArgumentParser(description='Generador de Check hosts Nagios')
parser.add_argument('ip_device', type=str,
                    help='ip del dipositivo')
parser.add_argument('ip_gateway', default='', type=str,
                    help='ip para hacerle salto')
parser.add_argument('vrf', default='default', type=str,
                    help='vrf')
parser.add_argument('filename', type=str,
                    help='nombre del archivo')
args = parser.parse_args()
print(args)
claro = Claro()

master = Master()

cisco = CiscoIOS(args.ip_device, "XR", master)
if args.ip_gateway != '':
    cisco.set_jump_gateway(args.ip_gateway, protocol="telnet")

# test3 = CiscoIOS("172.17.28.110", "XR", master)
# test2 = CiscoXR("172.16.30.253", "XR", master)


# test2.set_snmp_community()
# test2.set_yed_xy()
# print(test2.x)
claro.master = master
# xrs = CiscoXR.devices(master)


with open(args.filename, "w") as f:
    f.write(cisco.create_file_nagios_arp(vrf=args.vrf))

# devices = CiscoXR.devices(master)
# pprint(devices)
'''
devices,ips = claro.devices_from_network("172.16.30.0/24")

claro.excute_methods(methods={"set_snmp_location":{}},devices=devices)

pprint(len(devices))
data = [{"ip":device.ip,"hostname":device.hostname, "snmp_location":device.snmp_location} for device in devices]

claro.save_to_excel_list(data,file_name="snmp_location")
'''
