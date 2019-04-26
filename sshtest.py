from pprint import pprint
from pysnmp import hlapi
from tools import get_bulk_real_auto, get_oid_size
from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
from model.BGPNeigbor import BGPNeighbor
import time
from model.InterfaceUfinet import InterfaceUfinet

'''if_index,
                description,
                bandwith,
                l3_protocol,
                l3_protocol_attr
                ,l1_protocol,
                l1_protocol_attr,
                data_flow,
                net_device_uid'''

protocol_states = {1: 'up',
                   2: 'down',
                   3: 'testing',
                   4: 'unknown',
                   5: 'dormant',
                   6: 'notPresent',
                   7: 'lowerLayerDown'}

link_state = {1: 'up',
              2: 'down',
              3: 'testing'}


host = '172.16.30.250'

'''

real_oid = '1.3.6.1.2.1.31.1.1.1.6'
community = 'INTERNET_UFINET'
oid_64 = get_oid_size(target=host,  credentials=community,oid='1.3.6.1.2.1.31.1.1.1.6')
oid_32 = get_oid_size(target=host,  credentials=community,oid='1.3.6.1.2.1.2.2.1.7')
print(f'64 {oid_64} 32 {oid_32}')
'''
isp = ISP()
isp.master = Master()
device = CiscoXR(ip=host, display_name='a', master=isp.master)
device.set_snmp_community()

data = InterfaceUfinet.bulk_snmp_data_interfaces(device=device)
pprint(data)
community = 'INTERNET_UFINET'
# pprint( get_bulk_real_auto(target=host, oid='1.3.6.1.2.1.4.20.1.2', credentials=community))

'''
# device = CiscoXR(ip=host, display_name='a', master=isp.master)
# device.set_snmp_bgp_neighbors(special_community="INTERNET_UFINET",address_family=['ipv4','ipv6'])
time1 = time.time()
data1 = get_bulk_real_auto(target=host, oid=real_oid, credentials=community)
time.sleep(25)
time2 = time.time()
timelapse = float(time2 - time1)
data3 = [[registro[0], calculate_delta(new_counter=registro[1],
                                       old_counter=data1[index][1],
                                       timelapse=timelapse) * 8]
         for index, registro in enumerate(data2)]
         
pprint(data3[1])

def calculate_delta(old_counter, new_counter, timelapse):
    print(old_counter)
    print(new_counter)
    print(timelapse)
    new_counter = new_counter if new_counter >= old_counter else new_counter + 18446744073709551616
    return (new_counter - old_counter) / timelapse



'''
