from model.CiscoIOS import CiscoIOS
from model.ospf_adjacency import ospf_adjacency, add_ospf_adjacency
from lib.pyyed import *
from collections import defaultdict
from tools import logged
from threading import Thread
import os, shelve

@logged
class ospf_database:
    edge_roundness = {1: .05, 2: .05, 3: .15, 4: .15, 5: .25, 6: .25, 7: .35, 8: .35}

    def __init__(self, ip_seed_router, isp, process_id='1', area='0'):
        seed_router = CiscoIOS(ip=ip_seed_router, display_name='seed', master=isp.master)
        seed_router = isp.correct_device_platform([seed_router])[0]
        p2p, self.routers = seed_router.ospf_area_adjacency_p2p(process_id=process_id, area=area)
        self.verbose.warning(f"_INIT_ p2p :{len(p2p)} rourters {len(self.routers)}")
        self.isp = isp
        self.routers = [CiscoIOS(ip=router, display_name=router, master=self.isp.master) for router in self.routers]
        self.routers = isp.correct_device_platform(self.routers)
        self.routers = {router.ip: router for router in self.routers}

        self.isp.excute_methods(methods={"set_interfaces": {}},
                                devices=self.routers.values(), thread_window=35)
        self.isp.do_uni_methods(methods={"set_snmp_community": {}, "get_uid_save": {}}, devices=self.routers.values())
        self.isp.do_uni_methods(methods={"set_snmp_location_attr": {}}, devices=self.routers.values())
        self.graph = Graph()
        self.neighbors_occurrences_count = defaultdict(int)
        threads = []
        result_p2p = []
        for network, neighbors in p2p.items():
            kwargs = {"list_networks": result_p2p, 'network_id': network, 'ospf_database': self, 'neighbors': neighbors,
                      'network_type': 'p2p'}
            t = Thread(target=add_ospf_adjacency, kwargs=kwargs)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        self.p2p = {p2p.network_id: p2p for p2p in result_p2p}

        self.dev.info("OSPF DATABASE INIT FINISH")

    def get_yed_file(self, filename):

        for ip, router in self.routers.items():
            self.graph.nodes[router.ip] = router.get_yed_node()
        for network, p2p in self.p2p.items():
            self.graph.edges[network] = p2p.yed_edge()

        with open(filename + ".graphml", "w") as file:
            file.write(self.graph.get_graph())

    def get_vs(self):
        topology = {"nodes": [router.get_vs() for router in self.routers.values()],
                    "edges": [edge.get_vs() for edge in self.p2p.values()],
                    'options': self.get_vs_options()}

        return topology

    def get_vs_options(self):
        physics = {'enabled': True,
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
