from model.Devices import Devices
from config.Master import Master

ma = Master()

devs = Devices(master=ma, ip_list=['172.16.30.244'])

devs.set_interfaces_db()

esc = devs.devices['172.16.30.244']

print(esc.interfaces_ip.keys())
esc.set_interfaces_snmp()

print(esc.interfaces_ip.keys())

esc.correct_ip_interfaces()
