from config.Master import Master
from model.Diagram import Diagram

diagrams = ['_ospf_ufinet_regional',
            'RCE_GUATEMALA'
            ]
master = Master()

diagram = Diagram(master=master, name=diagrams[1])

diagram.get_newer_state()
devices = diagram.state.devices()
kwargs = {device.ip: {'set_interfaces_snmp': {'save': True, 'clear_memory': True}} for device in devices}
devices.execute(methods=['set_interfaces_snmp'], kwargs=kwargs, deferred=True)
