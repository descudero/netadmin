from model.CiscoIOS import CiscoIOS
from model.Devices import Devices
from config.Master import Master
from tools import real_get_bulk
from pprint import pprint
from model.InternetServiceProvider import InternetServiceProvider as ISP

master = Master()
c = CiscoIOS(master=master, ip='10.240.233.150', display_name="")
c.set_ip_bgp_neighbors()
isp = ISP()
pprint(c.bgp_neighbors)
isp.save_to_excel_list(list_data=c.bgp_neighbors, file_name='colombia_bgp')
