from config.Master import Master
from model.Diagram import Diagram

diagrams = ['_ospf_ufinet_regional'
            ]

master = Master()

for diagram_name in diagrams:
    diagram = Diagram(master=master, name=diagram_name)

    diagram.get_newer_state()
    devices = diagram.state.devices()
    kwargs = {device.ip: {'set_interfaces_snmp': {'save': True, 'clear_memory': True}} for device in devices}
    devices.execute(methods=['set_interfaces_snmp'], deferred=True)

for device in devices:
    print(f'{device.ip} i {len(device.interfaces)}')
