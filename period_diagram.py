from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
import ipaddress
from model.BGPNeigbor import BGPNeighbor
import time
from model.InterfaceUfinet import InterfaceUfinet
from model.Devices import Devices
from model.ospf_database import ospf_database
import datetime
from tools import PerformanceLog
from threading import Thread
from pprint import pprint

isp = ISP()
isp.master = Master()
isp.master.username = 'descuderor'
isp.master.password = 'Zekto2014-'
device = CiscoIOS(ip='172.16.30.5', display_name='a', master=isp.master, )
period_start = '2019-07-10 00:00:00'
base = datetime.datetime.strptime(period_start, '%Y-%m-%d %H:%M:%S')
x = 1
date_list = [str(base + datetime.timedelta(hours=x)) for x in range(0, 25)]

print(date_list)

regional = {
    "ip_seed_router": "172.16.30.5", "process_id": '1', "area": '0',
    'network_name': '_ospf_ufinet_regional'
}
guatemala = {
    "ip_seed_router": "172.17.22.52",
    "process_id": '502', "area": '502008', 'network_name': 'RCE_GUATEMALA'
}
lista = []
pf = PerformanceLog('24 hours diagram')
threads = []
dbs = []
data_final = []
for i in range(0, 24):
    period_start = date_list[i]
    period_end = date_list[i + 1]
    dbd = ospf_database(isp=isp, source='delay_start', period_start=period_start, period_end=period_end, **regional)
    dbs.append(dbd)
    t = Thread(target=dbd.delay_start)
    t.start()
    threads.append(t)

for t in threads:
    t.join()

for dbd in dbs:
    data = dbd.get_vs()
    data_final.append({'period': f'{dbd.period_start} - {dbd.period_end}', 'data': data})

pf.flag('end')

pf.print_intervals()
