from model.CiscoIOS import CiscoIOS
from config.Master import Master
from pprint import pprint
from model.InternetServiceProvider import InternetServiceProvider as ISP
import pickle
from model.Devices import Devices

master = Master()
isp = ISP()
# cisco = CiscoIOS(master=master, ip='10.240.233.154', display_name='mmm')
# cisco.community = 'pnrw-all'
# cisco.set_ip_bgp_neighbors()
# isp.save_to_excel_list(list(cisco.bgp_neighbors.values()),file_name='colombia_wbp_bgp')
#
# cisco2 = CiscoIOS(master=master, ip='172.17.28.164', display_name="rce")
# cisco2.set_pseudowires()
#
# pprint(cisco2.pseudowires)
#
# pseudo = {pw['vlan']: pw for pw in cisco2.pseudowires.values() if '0/2/1' in pw['interface']}
# pprint(pseudo)
# print(len(pseudo))
#
# interfaces = {index: {'index': index, 'description': interface.description, 'ip': interface.ip, 'mask': interface.mask}
#               for
#               index, interface in cisco.interfaces.items() if "BDI" in index}
#
# with open('co_sc', 'wb') as co:
#     pickle.dump({'pw': pseudo, 'interface': interfaces},file=co)
# print('guardo')
with open('co_sc', 'rb') as co:
    data = pickle.load(co)
    interfaces = data['interface']
    pseudo = data['pw']

ips = {pw['destination_ip'] for pw in pseudo.values()}
pprint(ips)
devs = Devices(master=master, ip_list=ips)
methods = ['set_pseudowires']
full_command = ""
devs.execute(methods=methods)

# table=[]
# full_command = ""
# command_failed = ""
# for interface in interfaces.values():
#     if "BD" in interface['index']:
#         try:
#             vlan_id = interface['index'].replace("BDI", "")
#             new_index = "BVI" + vlan_id
#             pw = pseudo[vlan_id]
#             command = f''' interface {new_index}
#                            description L3:CONCUS D:D L1:WR {interface['description'].strip()} pw:{pw['destination_ip']}:{pw['vc_id']}
#                            vrf INTERNET
#                            no shutdown
#                            ipv4 address {interface['ip']} {interface['mask']}
#                            load-interval 30
#                            l2vpn bridge group L3SERVICES bridge-domain VLAN{vlan_id}
#                            description {interface['description'].strip().replace(' ','_')}
#                            mtu {pw['remote_mtu']}
#                            routed interface {new_index}
#                            vfi V3LAN{vlan_id}
#                            neighbor {pw['destination_ip']} pw-id {pw['vc_id']} pw-class MPLS_DEFAULT
#                            root
#                                    '''
#             row = {'index': 'index',
#                    'ip': interface['ip'],
#                    'description': interface['description'],'command':command
#                    }
#             table.append(row)
#
#             full_command += command
#         except KeyError as e:
#             lan_id = interface['index'].replace("BDI", "")
#             new_index = "BVI" + vlan_id
#             command = f''' interface {new_index}
#             description L3:CONCUS D:D L1:WR {interface['description'].strip()}
#             vrf INTERNET
#             no shutdown
#             ipv4 address {interface['ip']} {interface['mask']}
#             load-interval 30
#             l2vpn bridge group L3SERVICES bridge-domain VLAN{vlan_id}
#             description {interface['description'].strip().replace(' ', '_')}
#             mtu 9180
#             routed interface {new_index}
#             vfi V3LAN{vlan_id} neighbor IPNEIH pw-id AJSDJ pw-class MPLS_DEFAULT
#             vfi V3LAN{vlan_id} neighbor IPNEIH pw-id AJSDJ pw-class MPLS_DEFAULT
#             root
#                                                '''
#             row = {'index': 'index',
#                    'ip': interface['ip'],
#                    'description': interface['description'], 'command': command
#                    }
#             table.append(row)
#
#             command_failed += command
#             pass
# isp.save_to_excel_list(table,file_name='colombia_wbp')
#
# with open('failed_script_colombia.txt', 'w') as f:
#     f.write(command_failed)

# with open('script_colombia.txt', 'w') as f:
#     f.write(full_command)
# interface BVI1853
# interface BVI1853 description L3:CONCUS D:D L1:WR CID:CRCRMET10037919I|METROWIRELESS|OCEANICA
# interface BVI1853 vrf INTERNET
# interface BVI1853 ipv4 address 186.179.69.138 255.255.255.254
# interface BVI1853 load-interval 30
# l2vpn bridge group TRUNKS bridge-domain VLAN1853
# l2vpn bridge group TRUNKS bridge-domain VLAN1853 mtu 9180
# l2vpn bridge group TRUNKS bridge-domain VLAN1853 vfi VLAN1853
# l2vpn bridge group TRUNKS bridge-domain VLAN1853 vfi VLAN1853 neighbor 172.17.26.10 pw-id 506185319
# l2vpn bridge group TRUNKS bridge-domain VLAN1853 vfi VLAN1853 neighbor 172.17.26.10 pw-id 506185319 pw-class MPLS_DEFAULT
# l2vpn bridge group TRUNKS bridge-domain VLAN1853 routed interface BVI1853
