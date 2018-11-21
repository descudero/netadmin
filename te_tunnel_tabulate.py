from __future__ import print_function

from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
from model.L3Path import L3Path
from model.claseClaro import Claro
from pprint import pprint
from multiping import multi_ping

claro = Claro()

from multiping import MultiPing

claro.set_master(username="descuderor", password="zekto2014-")

claro.tabulate_mpls_traffic_tunnels("172.16.30.3", filename="archivo_pco1")
