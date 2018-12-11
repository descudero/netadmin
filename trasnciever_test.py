from __future__ import print_function

from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
from model.L3Path import L3Path
from model.claseClaro import Claro
from pprint import pprint
from multiping import multi_ping

claro = Claro()
master = Master(password="zekto2014-", username="descuderor")
# test = CiscoXR("172.16.30.244","XR",master)

# print(test.set_arp_list(vrf="INTERNET"))
test2 = CiscoIOS("172.16.30.3", "IOS", master)
test2.set_interfaces_transciever_optics()
