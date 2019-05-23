from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master as ma
from model.Devices import Devices

isp = ISP()
master = ma()

isp.master = master

device = Devices.factory_device(master=master, ip='172.16.30.250')
device.set_snmp_community()
device.set_interfaces_snmp()
