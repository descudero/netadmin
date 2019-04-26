from pprint import pprint
from pysnmp import hlapi
from tools import get_bulk_real_auto
from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
from model.BGPNeigbor import BGPNeighbor
import time

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

_sql_state_columns = {'link_state': '1.3.6.1.2.1.2.2.1.7',
                      'protocol_state': '1.3.6.1.2.1.2.2.1.8',
                      'input_rate': '1.3.6.1.2.1.31.1.1.1.6',
                      'output_rate': '1.3.6.1.2.1.31.1.1.1.10',
                      'input_errors': '1.3.6.1.2.1.2.2.1.14',
                      'output_errors': '1.3.6.1.2.1.2.2.1.20'}

interface_description = "1.3.6.1.2.1.31.1.1.1.18"
interface_ip = '1.3.6.1.2.1.4.20.1.2'
interface_index = '1.3.6.1.2.1.2.2.1.2'
mtu = '1.3.6.1.2.1.2.2.1.4'
bandwidth = '1.3.6.1.2.1.31.1.1.1.15'

host = '172.16.30.250'
real_oid = '1.3.6.1.2.1.31.1.1.1.6'
community = 'INTERNET_UFINET'
# device = CiscoXR(ip=host, display_name='a', master=isp.master)
# device.set_snmp_bgp_neighbors(special_community="INTERNET_UFINET",address_family=['ipv4','ipv6'])
time1 = time.time()
data1 = get_bulk_real_auto(target=host, oid=real_oid, credentials=community)

time.sleep(15)
data2 = get_bulk_real_auto(target=host, oid=real_oid, credentials=community)
time2 = time.time()
timelapse = float(time2 - time1)
print(timelapse)


def calculate_delta(old_counter, new_counter, timelapse):
    print(old_counter)
    print(new_counter)
    print(timelapse)
    new_counter = new_counter if new_counter >= old_counter else new_counter + 18446744073709551616
    return (new_counter - old_counter) / timelapse


data3 = [[registro[0], calculate_delta(new_counter=registro[1],
                                       old_counter=data1[index][1],
                                       timelapse=timelapse) * 8]
         for index, registro in enumerate(data2)]
pprint(data3[1])
