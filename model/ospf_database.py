from model.CiscoIOS import CiscoIOS
from model.ospf_adjacency import ospf_adjacency
from lib.pyyed import *
from collections import defaultdict
from tools import logged


@logged
class ospf_database:
    edge_roundness = {1: .05, 2: .05, 3: .20, 4: .20, 5: .35, 6: .35, 7: .5, 8: .5}

    def __init__(self, ip_seed_router, isp, process_id='1', area='0'):
        seed_router = CiscoIOS(ip=ip_seed_router, display_name='seed', master=isp.master)
        seed_router = isp.correct_device_platform([seed_router])[0]
        p2p, self.routers = seed_router.ospf_area_adjacency_p2p(process_id=process_id, area=area)
        self.isp = isp
        self.routers = [CiscoIOS(ip=router, display_name=router, master=self.isp.master) for router in self.routers]
        self.routers = isp.correct_device_platform(self.routers)
        self.routers = {router.ip: router for router in self.routers}
        self.p2p = {}
        self.isp.excute_methods(methods={"set_interfaces": {}},
                                devices=self.routers.values(), thread_window=5)
        self.isp.excute_methods(methods={"set_snmp_community": {}, "get_uid_save": {}}, devices=self.routers.values())

        self.graph = Graph()
        self.neighbors_occurrences_count = defaultdict(int)
        self.verbose.warning("finish init  methods routers gone to edges")
        for network, neighbors in p2p.items():
            self.p2p[network] = ospf_adjacency(network_id=network, ospf_database=self, neighbors=neighbors,
                                               network_type='p2p')
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
                    'options':
                        {"edges": {"smooth": {"type": "discrete",
                                              "forceDirection": "vertical"}},
                         'physics': {'solver': "forceAtlas2Based",
                                     'enabled': False}}}

        return topology
