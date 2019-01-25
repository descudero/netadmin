from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
import time

isp = ISP()
isp.master = Master()

print(isp.ospf_topology_dict_vs_date())
