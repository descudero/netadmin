from model.CiscoIOS import CiscoIOS
from model.ospf_adjacency import ospf_adjacency
from lib.pyyed import *
from collections import defaultdict
from tools import logged
from threading import Thread
import os, shelve
from model.Devices import Devices
from model.Diagram import Diagram
import ipaddress


@logged
class ospf_database:
    edge_roundness = {1: .05, 2: .05, 3: .15, 4: .15, 5: .25, 6: .25, 7: .35, 8: .35}

    def __init__(self, ip_seed_router, isp, process_id='1', area='0', interface_method="interfaces_from_db_today",
                 network_name='ospf_regional'):
        self.area = area
        self.isp = isp
        self.diagram = Diagram(master=isp.master, name=network_name)
        seed_router = Devices.factory_device(master=self.isp.master, ip=ip_seed_router)

        p2p, routers = seed_router.ospf_area_adjacency_p2p(process_id=process_id, area=area)

        self.verbose.warning(f"_INIT_ p2p :{len(p2p)} rourters {len(routers)}")

        self.devices = Devices(master=self.isp.master, ip_list=routers)
        self.devices.execute_processes(methods=['set_snmp_location_attr'])
        self.devices.execute_processes(methods=['get_uid_save'], thread_window=15)
        self.devices.execute_processes(methods=[interface_method], thread_window=20)
        # self.devices.execute_processes(methods=['interfaces_from_db_today'], thread_window=15)

        self.graph = Graph()
        self.neighbors_occurrences_count = defaultdict(int)
        threads = []
        result_p2p = []

        for network, neighbors in p2p.items():
            kwargs = {"list_networks": result_p2p, 'network_id': network, 'ospf_database': self, 'neighbors': neighbors,
                      'network_type': 'p2p'}
            t = Thread(target=ospf_adjacency.add_ospf_adjacency, kwargs=kwargs)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        self.p2p = {p2p.network_id: p2p for p2p in result_p2p}
        p2p_down = self.ospf_down_interfaces()
        p2p_down_adj = []
        threads = []
        for network, neighbors in p2p_down.items():
            kwargs = {"list_networks": p2p_down_adj, 'network_id': network, 'ospf_database': self,
                      'neighbors': neighbors,
                      'network_type': 'p2p_down', 'state': 'down'}
            t = Thread(target=ospf_adjacency.add_ospf_adjacency, kwargs=kwargs)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        self.p2p_down_links = {}

        self.dev.info("OSPF DATABASE INIT FINISH")

    @property
    def routers(self):
        return self.devices.devices

    def ospf_down_interfaces(self):

        p2p = {}

        down_ospf_interfaces = [interface for device in self.devices for interface in device.interfaces.values() if
                                interface.link_state == 'down' and interface.l3_protocol == "MPLS" and interface.l3_protocol_attr == "OSP"]

        for interface in down_ospf_interfaces:
            net_id = str(ipaddress.IPv4Network(str(interface.ip) + "/30", strict=False).network_address)
            try:
                if net_id != "127.0.0.0":
                    if net_id in p2p:
                        if len(p2p[net_id]) == 1:
                            data = {'router_id': interface.parent_device.ip,
                                    'neighbor_ip': p2p[net_id]["s"]['router_id'],
                                    'interface_ip': str(interface.ip),
                                    'area': self.area,
                                    'metric': "100000",
                                    'network': net_id
                                    }
                            p2p[net_id].append(data)
                            p2p[net_id][0]['neighbor_ip'] = interface.parent_device.ip

                    else:

                        data = {'router_id': interface.parent_device.ip,
                                'interface_ip': str(interface.ip),
                                'area': self.area,
                                'metric': "100000",
                                'network': net_id
                                }
                        p2p[net_id] = [data]
                self.verbose.warning(f'set_down_mpls_interfaces p2p down {len(p2p)}')
            except Exception as e:
                self.dev.warning(f'set_down_mpls_interfaces {interface} error {e}')
        return p2p

    def get_yed_file(self, filename):

        for ip, router in self.routers.items():
            self.graph.nodes[router.ip] = router.get_yed_node()
        for network, p2p in self.p2p.items():
            self.graph.edges[network] = p2p.yed_edge()

        with open(filename + ".graphml", "w") as file:
            file.write(self.graph.get_graph())

    def get_vs(self):
        topology = {"nodes": [
            router.get_vs(x=self.diagram.devices_uid[router.uid]['x'] if router.uid in self.diagram.devices_uid
            else 0,
                          y=self.diagram.devices_uid[router.uid][
                              'y'] if router.uid in self.diagram.devices_uid
                          else 0,
                          ) for router in
            self.routers.values()],
            "edges": [edge.get_vs() for edge in self.p2p.values()],
            'options': self.get_vs_options()}

        return topology

    def get_vs_options(self):
        physics = {'enabled': False,
                   'solver': 'barnesHut',
                   'barnesHut': {
                       'gravitationalConstant': -2000,
                       'centralGravity': 0.3,
                       'springLength': 195,
                       'springConstant': 0.14,
                       'damping': 0.09,
                       'avoidOverlap': 1
                   }}
        edges = {"smooth": {"type": "discrete",
                            "forceDirection": "vertical"}}

        layout = {'randomSeed': 4444}

        return {'physics': physics, 'edges': edges, 'layout': layout}

    @staticmethod
    def get_vs_from_shelve(shelve_name):
        with shelve.open(shelve_name) as sh:
            try:
                dict_ospf = sh["db"]
                return dict_ospf
            except Exception as e:
                print("no able lo load shelve")
        return {"label": "no_data_in_date"}

    @staticmethod
    def save_xy(master, data):
        ids = data.keys()

        pass
