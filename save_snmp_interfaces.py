from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.Devices import Devices
from pprint import pprint
import argparse

isp = ISP()
isp.master = Master()

parser = argparse.ArgumentParser(description='Interfaces report saver')
parser.add_argument('host', type=str,
                    help='host_ip')
args = parser.parse_args()

ip = args.host
devices = list(iter(Devices(master=isp.master, ip_list=[ip])))[0]
devices.set_interfaces_snmp()
pprint(devices.interfaces)
