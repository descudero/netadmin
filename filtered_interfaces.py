from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.InterfaceUfinet import InterfaceUfinet

master = Master()
ip = "172.16.30.253"
isp = ISP()
isp.master = master
filters = {"if_index": "."}

device = isp.correct_device_platform(isp.devices_from_ip_list([ip]))[0]

device.set_interfaces()
device.save_interfaces_states(filters={'l3_protocol': 'BGP'})

# print(InterfaceUfinet.interfaces_uid(device=device,interfaces=device.interfaces.values()))
# interfaces = [interface for interface in  device.interfaces.values() if interface.uid==0]
# print(len(device.interfaces))
# print(len(interfaces))
