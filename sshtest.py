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
device = CiscoIOS(ip='172.17.22.52', display_name='a', master=isp.master)

dbd = ospf_database(ip_seed_router=device.ip, isp=isp, process_id='502', area='502008', network_name='RCE_GUATEMALA')

adjs = [adj
        for p2p in dbd.p2p.values() for adj in p2p.adj_neighbors.values()]

dict_data = []
dist_snmp = []
for adj in adjs:
    try:

        dict_data.append({"interface": adj['interface'].if_index,
                          "ip_dev": adj['router_id'], "description": adj['interface'].description,
                          "command": f"interface {adj['interface'].if_index} "
                          f"\n description L3:MPLOSP D:B L1:DP {adj['interface'].description}"})
    except Exception as e:
        dist_snmp.append(adj['router_id'])
        pprint(f' {adj} {e}')

dist_snmp = [{"ip": ip} for ip in dist_snmp]
isp.save_to_excel_list(list_data=dict_data, file_name='interfaces guatemala')
isp.save_to_excel_list(list_data=dist_snmp, file_name='no_snmp')
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
