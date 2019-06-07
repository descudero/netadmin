from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
import time
from pprint import pprint
from model.Devices import Devices
isp = ISP()
isp.master = Master()
isp.master.username = "descuderor"
isp.master.password = "Zekto2014-"
ips = [line.replace("\n", "") for line in open("hosts/interfaces/guatemala")]
# devs = Devices(master=isp.master,ip_list=ips,check_up=False)

# devs.execute_processes(methods=["fix_interfaces_attr"],thread_window=20)
c = CiscoIOS(ip="172.17.22.53", master=isp.master, display_name="")
c.set_snmp_community()
c.set_interfaces_snmp()
interfaces = list(c.interfaces.values())
