from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
import time

isp = ISP()
isp.master = Master()

print(isp.ospf_topology_vs(ip_seed_router="172.16.30.5"))

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
