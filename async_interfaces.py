from model.Devices import Devices
from config.Master import Master
from model.Diagram import Diagram
import asyncio
import datetime

with open('hosts/interfaces/regional') as f:
    ip_lista = [line.replace('\n', '') for line in f]

master = Master()

diagrams = Diagram.recent_diagrams(master)
date_last_ten_minutes = str(datetime.datetime.now() - datetime.timedelta(minutes=60))
sql = f'''SELECT net_device_uid from poll_events where timestamp>'{date_last_ten_minutes}' '''
connection = master.db_connect()
with connection.cursor() as cursor:
    cursor.execute(sql)
    data = cursor.fetchall()
    uids = {row['net_device_uid'] for row in data}
window = 10
for diagram in diagrams:
    not_polled = set(diagram.state.devices_uid.keys()).difference(uids)
    if not_polled:
        ips = [diagram.state.devices_uid[k].ip for k in not_polled]
        ips_uid = {diagram.state.devices_uid[k].ip: k for k in not_polled}
        top_ten_ips = ips[0:window - 1] if len(ips) > window else ips
        ips_uid = {ip: ips_uid[ip] for ip in top_ten_ips}
        break

#
#
devs = Devices(master=Master(), ip_list=top_ten_ips, check_up=True)
for dev in devs:
    dev.uid = ips_uid[dev.ip]
devs.add_snmp_event(event='interfaces', type='asyc')
#
#
asyncio.get_event_loop().run_until_complete(devs.interfaces_async())
#
#
# devs.save_interfaces()
