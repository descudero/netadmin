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
from pprint import pprint
from collections import ChainMap
from threading import Lock


@logged
class ospf_database:
    edge_roundness = {1: .05, 2: .05, 3: .15, 4: .15, 5: .25, 6: .25, 7: .35, 8: .35, 9: .375, 10: .375}

    def __init__(self, ip_seed_router, isp, process_id='1', area='0', interface_method="interfaces_from_db_today",
                 network_name='ospf_regional', source="real_time"):
        self.area = area
        self.isp = isp
        self.diagram = Diagram(master=isp.master, name=network_name)
        lock = Lock()
        if source == 'real_time':
            seed_router = Devices.factory_device(master=self.isp.master, ip=ip_seed_router)

            p2p, routers = seed_router.ospf_area_adjacency_p2p(process_id=process_id, area=area)
            self.devices = Devices(master=self.isp.master, ip_list=routers, check_up=False)
            self.devices.execute_processes(methods=['set_snmp_location_attr'])
            self.devices.set_uids()
            self.verbose.warning(f"_INIT_real_time  p2p :{len(p2p)} rourters {len(routers)}")

        # elif source =='last_state':
        elif source == "db":
            self.diagram.get_newer_state()
            self.devices = self.diagram.state.devices()
            p2p = self.diagram.state.p2p()
            self.verbose.warning(f"_INIT_ db  p2p:{len(p2p)} dev:{len(self.devices)}")
        self.devices.set_interfaces_db()

        self.graph = Graph()
        self.neighbors_occurrences_count = defaultdict(int)
        threads = []
        result_p2p = []
        self.verbose.warning(f"__INIT__Fishish diagram.state.p2p  {len(p2p)} ")
        for network, neighbors in p2p.items():
            kwargs = {'lock': lock, "list_networks": result_p2p, 'network_id': network, 'ospf_database': self,
                      'neighbors': neighbors,
                      'network_type': 'p2p'}

            t = Thread(target=ospf_adjacency.add_ospf_adjacency, name=network, kwargs=kwargs)
            t.start()
            threads.append(t)
        for index, t in enumerate(threads):
            self.verbose.warning(f"tried p2p {index} {t.name} ")
            t.join()
            self.verbose.warning(f"joined p2p {index} {t.name} ")

        self.verbose.warning(f"__INIT__Fishish join add_ospf_adjacency p2p {len(result_p2p)} ")
        self.p2p = {p2p.network_id: p2p for p2p in result_p2p}
        self.verbose.warning(f"__INIT__Fishish join add_ospf_adjacency real p2p {len(self.p2p)} ")

        if source == 'real_time':
            self.p2p_down_links = self.ospf_down_interfaces()
            p2p_down_adj = []
            threads = []
            for network, neighbors in self.p2p_down_links.items():
                kwargs = {'lock': lock, "list_networks": p2p_down_adj, 'network_id': network, 'ospf_database': self,
                          'neighbors': neighbors,
                          'network_type': 'p2p_down', 'state': 'down'}
                t = Thread(target=ospf_adjacency.add_ospf_adjacency, kwargs=kwargs)
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
            self.p2p_down_links = {p2p.network_id: p2p for p2p in p2p_down_adj}
            self.verbose.warning(f'OSPF LINKS DOWN {len(self.p2p_down_links)}')
        else:
            self.p2p_down_links = {}

        self.verbose.warning("OSPF DATABASE INIT FINISH")

    @property
    def adjacencies(self):
        return ChainMap(self.p2p, self.p2p_down_links)

    @property
    def routers(self):
        return self.devices.devices

    def ospf_down_interfaces(self):

        p2p = {}
        down_ospf_interfaces = [interface for device in self.devices for interface in device.interfaces.values() if
                                (interface.protocol_state == 'down' or interface.link_state == 'down')
                                and interface.l3_protocol == "MPLS"
                                and interface.l3_protocol_attr == "OSP"]

        for interface in down_ospf_interfaces:
            net_id = str(ipaddress.IPv4Network(str(interface.ip) + "/30", strict=False).network_address)
            if interface.parent_device.ip in []:
                self.verbose.warning(f' nt:{net_id} n:{interface.parent_device.ip} i:{interface.ip}')
            try:
                if net_id != "127.0.0.0":

                    if net_id in p2p:

                        if len(p2p[net_id]) == 1:
                            data = {'router_id': interface.parent_device.ip,
                                    'neighbor_ip': p2p[net_id][0]['router_id'],
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
                self.verbose.debug(
                    f'set_down_mpls_interfaces p2p down {net_id} {interface.parent_device.ip} {len(p2p)}')
            except Exception as e:
                self.verbose.warning(f'set_down_mpls_interfaces {interface} error {e}')
        return p2p

    def get_yed_file(self, filename):

        for ip, router in self.routers.items():
            self.graph.nodes[router.ip] = router.get_yed_node()
        for network, p2p in self.p2p.items():
            self.graph.edges[network] = p2p.yed_edge()

        with open(filename + ".graphml", "w") as file:
            file.write(self.graph.get_graph())

    def get_vs(self):
        edges = [edge.get_vs() for edge in self.p2p.values()]
        edges_down = [edge.get_vs() for edge in self.p2p_down_links.values()]
        topology = {"nodes": [
            router.get_vs() for router in
            self.routers.values()],
            "edges": edges + edges_down,
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

    def save_state(self):
        self.diagram.save_state(devices=self.devices, adjacencies=self.adjacencies)
