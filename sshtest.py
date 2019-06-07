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
from model.Diagram import DiagramState, Diagram
import tools
from collections import Counter
from collections import defaultdict
import pickle

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

isp = ISP()
isp.master = Master()
isp.master.username = 'descuderor'
isp.master.password = 'Zekto2014-'
device = CiscoIOS(ip='172.16.30.5', display_name='a', master=isp.master, )

regional = {
    "ip_seed_router": "172.16.30.15", "process_id": '1', "area": '0',
    'network_name': '_ospf_ufinet_regional'
}
guatemala = {
    "ip_seed_router": "172.16.30.",
    "process_id": '502', "area": '502008', 'network_name': 'RCE_GUATEMALA'
}
dbd = ospf_database(isp=isp, source='real_time', **regional)

dbd.save_state()

# with open("ip_routers_gt", "r") as f:
#     ips = [line.replace("\n", "") for line in f]
#
# devs = Devices(ip_list=ips, master=isp.master, check_up=True)
# data = [{"ip": dev.ip, "com": dev.community} for dev in devs]
# isp.save_to_excel_list(list_data=data, file_name="snmp_gt_data")

#
# data = []
# def_dict = defaultdict(list)
# prepend = "interface "
# suffix = "description L3:MPLOSP D:B L1:DP "
# for network, adj in dbd.adjacencies.items():
#     try:
#         s = {'ip': adj.s_device.ip,
#              'config': f' {prepend} {adj.s_interface.if_index} \n {suffix} {adj.s_interface.description}'}
#
#     except:
#         s = {'ip': adj.s_device.ip, 'config': adj.s["interface_ip"]}
#     try:
#         t = {'ip': adj.t_device.ip,
#              'config': f' {prepend} {adj.t_interface.if_index} \n {suffix} {adj.t_interface.description}'}
#     except:
#         t = {'ip': adj.t_device.ip, 'config': adj.t["interface_ip"]}
#
#     data.append(s)
#     data.append(t)
#     try:
#         if adj.s_interface.l3_protocol == "UNKNOWN":
#             def_dict[t['ip']].append(t["config"])
#     except:
#         pass
#     try:
#         if adj.t_interface.l3_protocol == "UNKNOWN":
#             def_dict[s['ip']].append(s["config"])
#     except:
#         pass
#
# pickle.dump(def_dict,open( "gt.p", "wb" ))
# pprint(def_dict)
# def_dict = pickle.load(open( "gt.p", "rb" ))
# ips = list(def_dict.keys())
# pprint(ips)
# pprint(len(ips))

# data_config = {}
#
# for ip, data in def_dict.items():
#
#     interfaces = [row for row in data if row.count('L3:') == 1]
#     if interfaces:
#         dv = CiscoIOS(ip=ip, display_name="", master=isp.master)
#
#         command = "configure terminal \n\n"+"\n".join(interfaces) + "\nend\n wr"
#         data_config[ip]=command
#         dv.auto_send_command(command=command)
#
#     # dbd.devices.devices[ip].auto_send_command(command=command)
# pickle.dump(def_dict,open( "gt2.p", "wb" ))
# pprint(data_config)

# isp.save_to_excel_list(list_data=data, file_name="gt_config")

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

master = Master()
isp = ISP()
isp.master = Master()

# dbd = ospf_database(ip_seed_router='172.16.30.5', isp=isp, process_id='1', area='0',
#                  network_name='_ospf_ufinet_regional',source='db')

# dbd.save_state()
#
# dia = Diagram(name='_ospf_ufinet_regional', master=master)
# dia.get_newer_state()
# devices = dia.state.devices()
# devices.execute(methods=['set_snmp_location_attr'])
# for device in devices:
#     device.update_db()

'''
oid = "1.3.6.1.2.1.2.2.1.2"
community = 'uFi08NeT'
ip1 = '172.16.30.250'
data_bind1 = []
data = [{"ip": '172.17.22.28', "community": 'uFi08NeT', 'oid': "1.3.6.1.2.1.31.1.1.1.18", 'data_bind': []},
        {"ip": '172.16.30.250', "community": 'uFi08NeT', 'oid': "1.3.6.1.2.1.31.1.1.1.18", 'data_bind': []},
        ]
ips = ['172.16.30.246']

dev = Devices(master=Master(), ip_list=ips)
dev.execute(methods=['interfaces_from_db_today'], deferred_seconds=5, deferred=True)

for device in dev:
    mpls_interfaces = [interface for interface in device.interfaces.values() if interface.l3_protocol == 'MPLS']
    for interface in mpls_interfaces:
        print(f' interface {interface}')

threads = []
'''
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
