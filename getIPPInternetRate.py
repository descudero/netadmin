# imports


import threading

from config.Master import Master
from model.CiscoXR import CiscoXR

master = Master(password="zekto2014-", username="descudero")

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

filter = ["prepend", "pass"]
data_result = {}

threads = []
results = []
for name, ipp in ipps.items():
    t = threading.Thread(target=ipp.print_policy_map_rate_distribution, kwargs={"results": results})
    threads.append(t)
    t.start()

for i in range(len(threads)):
    threads[i].join()
print("\n".join(results))
