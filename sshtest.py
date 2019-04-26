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
                      'input_rate': '1.3.6.1.2.1.2.2.1.10',
                      'output_rate': '1.3.6.1.2.1.2.2.1.16',
                      'input_errors': '1.3.6.1.2.1.2.2.1.14',
                      'output_errors': '1.3.6.1.2.1.2.2.1.20'}

interface_description = "1.3.6.1.2.1.31.1.1.1.18"
interface_ip = '1.3.6.1.2.1.4.20.1.2'
interface_index = '1.3.6.1.2.1.2.2.1.2'
mtu = '1.3.6.1.2.1.2.2.1.4'
bandwidth = '1.3.6.1.2.1.31.1.1.1.15'

isp = ISP()
isp.master = Master()
host = '172.16.30.250'
real_oid = '1.3.6.1.2.1.2.2.1.10'
community = 'INTERNET_UFINET'
device = CiscoXR(ip=host, display_name='a', master=isp.master)
# device.set_snmp_bgp_neighbors(special_community="INTERNET_UFINET",address_family=['ipv4','ipv6'])

# data =get_bulk_real_auto(target=host,oid=real_oid,credentials=community)
# pprint(data)


print(isp.master.password)
print(isp.master.username)
print(Master.encode(key='pinf con vrf', hash='Ufinet18_2'))
