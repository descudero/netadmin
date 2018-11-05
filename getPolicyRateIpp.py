# imports
import getpass;

from config.Master import Master
from model.CiscoXR import CiscoXR

master = Master(password="descudero", username="zekto2014-")

# pba = CiscoDevice("PBAIPP",'C:\\Users\\descudero\\pba.txt')
# blu = CiscoDevice("BLUIPP",'C:\\Users\\descudero\\blu.txt')
# gdv = CiscoDevice("GDVIPP",'C:\\Users\\descudero\\gdv.txt')
##print(cisco.interfaces)
# print(cisco.route_policies)
# print(cisco.prefix_sets)
# interfaces = pba.route_policy_perInterface()

pba = CiscoXR("10.192.0.27", "pba", master)
blu = CiscoXR("10.192.0.146", "blu", master)
gdv = CiscoXR("10.192.0.22", "gdv", master)

# rate=pba.getSummarizeRate()
output = pba.print_policy_map_rate_distribution(printit=False)
output += blu.print_policy_map_rate_distribution(printit=False)
output += gdv.print_policy_map_rate_distribution(printit=False)
print(output)

getpass._raw_input(prompt=' presionar para terminar  ')
