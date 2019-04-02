from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master

master = Master()
ip = "172.16.30.253"
isp = ISP()
isp.master = master
filters = {"if_index": "."}

device = isp.correct_device_platform(isp.devices_from_ip_list([ip]))[0]

device.set_interfaces()

interfaces = [interface.dict for interface in device.interfaces if
              "." in interface.if_index and
              (interface.util_in > 0 or interface.util_out > 0)
              ]

isp.save_to_excel_list(interfaces, file_name=f'z{ip}_interfaces')
