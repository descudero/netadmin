# imports

import getpass;
import threading

from config.Master import Master
from model.CiscoXR import CiscoXR

ip = "186.151.62.1"
print("prueba")
master = Master(password="zekto2014-", username="descudero")
print("prueba2")

# pba = CiscoDevice("PBAIPP",'C:\\Users\\descudero\\pba.txt')
# blu = CiscoDevice("BLUIPP",'C:\\Users\\descudero\\blu.txt')
# gdv = CiscoDevice("GDVIPP",'C:\\Users\\descudero\\gdv.txt')
##print(cisco.interfaces)
# print(cisco.route_policies)
# print(cisco.prefix_sets)
# interfaces = pba.route_policy_perInterface()

ipps = {}
ipps["pba"] = CiscoXR("10.192.0.27", "pba", master)
ipps["blu"] = CiscoXR("10.192.0.146", "blu", master)
ipps["gdv"] = CiscoXR("10.192.0.22", "gdv", master)

filter = ["pass", "pre-"]
data_result = {}

threads = []
for name, ipp in ipps.items():
    t = threading.Thread(target=ipp.route_policy_per_interface)
    threads.append(t)
    t.start()

for t in threads:
    t.join()
for name, ipp in ipps.items():
    data_result[name] = ipp.ip_address_in_bgp_out_policy(ip, filter)

for name_ipp, interfaces in data_result.items():
    print("ipp " + name_ipp)
    for name_interface, interface in interfaces.items():
        print("\tinterface " + name_interface)
        print("\t policy " + interface["policy"].name)
        for prefix_name, prefix in interface["prefixsets"].items():
            print("\t\tprefix " + prefix_name)

getpass._raw_input(" presione para terminar *")

# print(pba.get_interfaces_rate_in())
