from model.CiscoIOS import CiscoIOS
from model.Devices import Devices
from config.Master import Master
from tools import real_get_bulk
from pprint import pprint
from model.InternetServiceProvider import InternetServiceProvider as ISP
import pickle

master = Master()
c = CiscoIOS(master=master, ip='10.240.233.150', display_name="")
c.set_service_instances()
c.set_bridge_domains(template_name_b="show bridge-domain ios_1000.template")
c.set_snmp_community()
c.set_interfaces_snmp()

filtered_interfaces = [interface for interface in c.interfaces.values()
                       if "BDI" in interface.if_index and interface.up]

# data_bind = []
#
# real_get_bulk(oid='1.3.6.1.2.1.4.20.1.3',community='pnrw-all',ip='10.240.233.150',data_bind=data_bind, id_ip=True)
#
# print(data_bind)
# print(len(data_bind))

pprint(c.service_instances)
data = []
data_interfaces = {'Te0/2/0': 'Te0/0/0/2', 'Te0/1/0': 'Te0/0/0/1'}

for interface in filtered_interfaces:
    try:
        phy_interface, encapsulation = c.bdi_bridge_domain[interface.if_index].get_first_interface()

    except:
        phy_interface = None
        encapsulation = ''

    if not phy_interface is None:
        try:
            new_interface = data_interfaces[phy_interface]
        except:

            new_interface = "NA"
        try:
            vlan = c.service_instances[f'{phy_interface}:{encapsulation}']['vlan']
        except Exception as e:
            print(f'error vlan {e}')
            vlan = "NA"
        command = f'interface {new_interface}.{encapsulation} \n' \
            f'description {interface.description} P:{interface.if_index}\n' \
            f'vrf INTERNET  \n' \
            f'proxy-arp  \n' \
            f'ipv4 address {str(interface.ip)} {str(interface.mask)} \n' \
            f' encapsulation dot1q {vlan}\n'

        row = {"before_fisical_interface": phy_interface,
               "new_fisical_interface": phy_interface,
               "int": interface.if_index,
               "ip": str(interface.ip), "des": interface.description, "command": command}

        data.append(row)

isp = ISP()

isp.save_to_excel_list(list_data=data, file_name='colombia')
