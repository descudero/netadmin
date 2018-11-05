from __future__ import print_function

from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
from model.L3Path import L3Path
from model.claseClaro import Claro
from pprint import pprint

claro = Claro()
master = Master(password="zekto2014-", username="descuderor")
test = CiscoXR("10.235.252.18", "XR", master)
claro.set_master(password="zekto2014-", username="descuderor")
claro.init_bgp_pe()
claro.set_bgp_neighbors(address_family="ipv4 unicast", vrf="INTERNET")
