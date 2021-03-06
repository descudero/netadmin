from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.Devices import Devices
from pprint import pprint
import argparse
import ipaddress
isp = ISP()
isp.master = Master()

parser = argparse.ArgumentParser(description='Interfaces report saver')
parser.add_argument('host', type=str,
                    help='host_ip')
args = parser.parse_args()

ip = args.host
print(ip)
device = list(iter(Devices(master=isp.master, ip_list=[ip])))[0]
device.set_snmp_community()
device.set_snmp_location_attr()
device.set_interfaces_snmp()
device.save_interfaces()
