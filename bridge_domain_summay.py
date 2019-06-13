from model.CiscoIOS import CiscoIOS
from config.Master import Master
from pprint import pprint
from model.InternetServiceProvider import InternetServiceProvider as ISP
import pickle

master = Master()
c = CiscoIOS(master=master, ip='10.240.233.150', display_name="")
c.set_bridge_domains(template_name_b="show bridge-domain ios_1000.template")
c.set_snmp_community()
c.set_interfaces_snmp()
filtered_interfaces = [interface for interface in c.interfaces.values()
                       if "BDI" in interface.if_index]
data = []
data_interfaces = {'Te0/2/0': 'Te0/0/0/2', 'Te0/1/0': 'Te0/0/0/1'}

for interface in filtered_interfaces:
    try:
        db_interface, encapsulation = c.bdi_bridge_domain[interface.if_index].get_first_interface()

    except:
        db_interface = None
        encapsulation = ''

    if not db_interface is None:
        try:
            new_interface = data_interfaces[db_interface]
        except:
            new_interface = "NA"
        command = f'interface {new_interface}.{encapsulation} \n' \
            f'ip address {str(interface.ip)} {str(interface.mask)} \n'

        row = {"fisical_interface": db_interface,
               "int": interface.if_index,
               "ip": str(interface.ip), "des": interface.description, "command": command}

        data.append(row)

isp = ISP()

isp.save_to_excel_list(list_data=data, file_name='colombia')
