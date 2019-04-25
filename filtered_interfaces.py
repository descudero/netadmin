from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.InterfaceUfinet import InterfaceUfinet
from pprint import pprint
from operator import itemgetter
master = Master()
ip = "172.16.30.253"
isp = ISP()
isp.master = master
filters = {"if_index": "."}
filter_keys = {'OSPF_MPLS': {'l3p': 'MPLS', 'l3a': 'OSP'}}
# device = isp.correct_device_platform(isp.devices_from_ip_list([ip]))[0]

# device.set_interfaces()
# device.save_interfaces_states(filters={'l3_protocol': 'BGP'})

# print(InterfaceUfinet.interfaces_uid(device=device,interfaces=device.interfaces.values()))
# interfaces = [interface for interface in  device.interfaces.values() if interface.uid==0]
# print(len(device.interfaces))
# print(len(interfaces))

data = InterfaceUfinet.interface_states_data_by_date(master=master, initial_date='2019-4-17', end_date='2019-4-24',
                                                     filter_keys=filter_keys)

pprint(data['OSPF_MPLS'][0:10])
isp.save_to_excel_list(list_data=data['OSPF_MPLS'], file_name='test_interface_data2')
