from pprint import pprint
from pysnmp import hlapi
from tools import get_bulk_real_auto, get_oid_size
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
from tools import real_get_bulk
import pysnmp

'''if_index,
                description,
                bandwith,
                l3_protocol,
                l3_protocol_attr
                ,l1_protocol,
                l1_protocol_attr,   
                data_flow,
                net_device_uid'''
'''

list_dev = ['172.16.30.4', '172.16.30.3', '172.16.30.1']
date = time.strftime("%Y%m%d")
parameters= {
        "ip_seed_router": "172.16.30.15",
        "shelve_name": "shelves/" + date + "_ospf_ufinet_regional"
    }
data =isp.ospf_topology_vs(**parameters)
'''
'''
isp = ISP()
isp.master = Master()
device = CiscoIOS(ip='172.16.30.5', display_name='a', master=isp.master)

dbd = ospf_database(ip_seed_router=device.ip, isp=isp, process_id='1', area='0')

pprint(dbd.ospf_down_interfaces())
'''
# device.set_interfaces()
# InterfaceUfinet.interfaces_uid(device,device.interfaces.values())


# data = device.dict_from_sql(sql='select * from interfaces where uid=1')

# pprint(data)
# bgp = BGPNeighbor.load_uid(isp=isp,uid='26572')
# data= BGPNeighbor.bgp_peers_from_db()
# pprint(len(data))
'''
real_oid = '1.3.6.1.2.1.31.1.1.1.6'
community = 'uFi08NeT'
oid_64 = get_bulk_real_auto(target=host,  credentials=community,oid='1.3.6.1.2.1.31.1.1.1.15')
pprint(oid_64)


device = CiscoIOS(ip='172.16.30.1', display_name='a', master=isp.master)
device.set_snmp_community()
device.set_interfaces_snmp()
interfaces = {interface.if_index:interface for interface in device.interfaces.values() if "." not in interface.if_index
              and "Te" in interface.if_index and "-" not in interface.if_index }
pprint(interfaces)

'''
# pprint(f'rate_int {interface.util_in} inpute rate {interface.input_rate} bw {interface.bw} ')


# data = InterfaceUfinet.bulk_snmp_data_interfaces(device=device)
# pprint(data)
# community = 'INTERNET_UFINET'
# pprint( get_bulk_real_auto(target=host, oid='1.3.6.1.2.1.4.20.1.2', credentials=community))
# device = CiscoXR(ip=host, display_name='a', master=isp.master)
# device.set_snmp_bgp_neighbors(special_community="INTERNET_UFINET",address_family=['ipv4','ipv6'])

import asyncio
from pysnmp.hlapi import *
import time

import threading

oid = "1.3.6.1.2.1.2.2.1.2"
community = 'uFi08NeT'
ip1 = '172.16.30.250'
data_bind1 = []
data = [{"ip": '172.17.22.28', "community": 'uFi08NeT', 'oid': "1.3.6.1.2.1.31.1.1.1.18", 'data_bind': []},
        {"ip": '172.16.30.250', "community": 'uFi08NeT', 'oid': "1.3.6.1.2.1.31.1.1.1.18", 'data_bind': []},
        ]
ips = [ip.replace("\n", '') for ip in open('bgp_pe_list', "r")]

dev = Devices(master=Master(), ip_list=ips)
dev.execute(methods=['set_interfaces_snmp'], deferred_seconds=5, deferred=True)

for device in dev:
    print(f' {device.ip} {len(device.interfaces)}')

threads = []
# data =[{"ip":ip.replace("\n",''),"community":'uFi08NeT','oid':"1.3.6.1.2.1.31.1.1.1.18",'data_bind':[]} for ip in open('bgp_pe_list',"r")]
# real_get_bulk(**data[0])

'''
for kwargs in data:
    print(f"{kwargs['ip']}")
    for line in kwargs['data_bind']:
        print(line)
for kwargs in data:
   t=threading.Thread(target=real_get_bulk, kwargs=kwargs)
   t.start()
   threads.append(t)

for t in threads:
    t.join()
'''
