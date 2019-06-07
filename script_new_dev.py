from model.Devices import Devices
from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
from model.InternetServiceProvider import InternetServiceProvider as ISP
import ipaddress
import pickle
from pprint import pprint

isp = ISP()
isp.master = Master()
isp.master.username = "descuderor"
isp.master.password = "Zekto2014-"
ips = [line.replace("\n", "") for line in open("hosts/interfaces/guatemala")]
# devs = Devices(master=isp.master,ip_list=ips,check_up=False)

# devs.execute_processes(methods=["fix_interfaces_attr"],thread_window=20)
c = CiscoIOS(ip="172.16.30.244", master=isp.master, display_name="")

c.set_snmp_community()
c.set_interfaces_snmp()
networks = ['186.179.71.', '186.179.73.', '186.179.79.']
interfaces_filtered = []
for ip, interface in c.interfaces.items():
    for net in networks:
        if net in str(interface.ip):
            interfaces_filtered.append(interface)

data = "\n".join(
    [f'{str(interface.ip)} {interface.if_index} {interface.description}' for interface in interfaces_filtered])

with open("clientes_cr.txt", "w") as f:
    f.write(data)
