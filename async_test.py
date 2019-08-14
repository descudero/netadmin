from model.Devices import Devices
from config.Master import Master
from model.Diagram import Diagram
import asyncio
import datetime

top_ten_ips = ['172.16.30.247']
#
devs = Devices(master=Master(), ip_list=top_ten_ips, check_up=False)
devs.devices['172.16.30.247'].uid_db()

devs.add_snmp_event(event='interfaces', type='asyc')

devs.devices['172.16.30.247'].community = 'pnrw-all'
devs.execute(methods=['set_interfaces_snmp'])
#
#
# asyncio.get_event_loop().run_until_complete(devs.set_interfaces_snmp())

print(devs.devices['172.16.30.247'].interfaces['BVI2150'].util_in)
#
#
