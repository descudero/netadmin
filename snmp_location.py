import textfsm
from pprint import pprint
from model.claseClaro import Claro
from config.Master import Master
import threading as th

fsm = textfsm.TextFSM(open("resources/templates/yed.template"))
file_data = open("resources/output_test/graph.txt").read()
fsm_results = fsm.ParseText(file_data, )

values = [dict(zip(fsm.header, row)) for row in fsm_results]
claro = Claro()
ip_devices = {row["ip"]: row for row in values}
claro.set_master(password="zekto2014-",
                 username="descuderor")
pprint(values)
devices = claro.devices_from_ip_list(ip_devices.keys())
devices = claro.correct_device_platform(devices)

threads = []
for device in devices:
    t = th.Thread(target=device.configure_snmp_location,
                  kwargs={"text": "x:" + ip_devices[device.ip]["x"] + ",y:" + ip_devices[device.ip]["y"]})
    t.start()
    threads.append(t)
for t in threads:
    t.join()
