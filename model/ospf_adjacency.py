import lib.pyyed as pyyed
from colour import Color
from tools import logged
import os
import shelve
from pprint import pprint


@logged
class ospf_adjacency:
    __l1 = {"MAYA": "#228B22",
            "LEVEL3": "#FF00FF",
            "CENTURY": "#FF1493",
            "TELXIUS": "#8B4513",
            "LANAUTILUS": "#BC8F8F",
            "DEF": "#00BFFF", "DOWN": "#333333"

            }

    __columns__ = ['network_id', 'diagram_state_uid', 'net_device_1_ip', 'interface_1_uid', 'interface_1_ip',
                   'interface_1_weight',
                   'interface_2_uid', 'net_device_2_ip', 'interface_2_ip', 'interface_2_weight']

    __table__ = "diagram_state_adjacencies"

    def __init__(self, network_id, ospf_database, neighbors, network_type='p2p', state='up'):
        self.uid = 0
        self.diagram_state = None
        self.state = state
        self.verbose.debug("net " + network_id + " start init ")
        self.network_id = network_id
        self.network_type = network_type
        self.ospf_database = ospf_database
        self.adj_neighbors = {}
        self.reversed = False
        self.neighbors_dict = {neighbor["router_id"]: neighbor for neighbor in neighbors}
        for neighbor in neighbors:
            neighbor_key = "s"
            if 's' in self.adj_neighbors:
                neighbor_key = 't'
            device = self.ospf_database.routers[neighbor["router_id"]]

            self.adj_neighbors[neighbor_key] = neighbor
            try:
                self.adj_neighbors[neighbor_key]["interface"] = device.interfaces_ip[neighbor["interface_ip"]]
                try:
                    setattr(self, f'{neighbor_key}_ip', self.adj_neighbors[neighbor_key]["interface"].ip)
                except Exception as e:
                    self.dev.warning(f'ops_adjacenfy __init__  no ip {neighbor_key}_ip')
            except KeyError:
                self.adj_neighbors[neighbor_key]["interface"] = "null"
                self.dev.warning(f'ospf_adjacncy no interface ip')
            self.adj_neighbors[neighbor_key]["network_device"] = device
        pair = self.pair_id()

        self.ospf_database.neighbors_occurrences_count[pair] += 1
        self.roundness = self.ospf_database.edge_roundness[self.ospf_database.neighbors_occurrences_count[pair]]
        if self.ospf_database.neighbors_occurrences_count[pair] % 2 == 0:
            self.reversed = True
            self.adj_obj_list()
            self.verbose.debug(" net_id reversed ")
        else:
            self.verbose.debug(" net_id not reversed ")
        # self.adj_neighbors["s"]["network_device"].add_p2p_ospf(self,self.adj_neighbors["t"])
        # self.adj_neighbors["t"]["network_device"].add_p2p_ospf(self,self.adj_neighbors["s"])
        self.dev.info("adjacency " + pair + " inited")
        self.set_vs()

    def __repr__(self):
        return str(self.__class__) + " NET " + self.network_id + " " + self.network_type + " N " + str(
            len(self.adj_neighbors))

    @property
    def master(self):
        self.ospf_database.isp.master

    def edge_label(self, orient='source'):
        index = 0 if orient == 'source' else 1
        adj = self.adj_ob[index]
        try:
            input_rate, output_rate = adj["interface"].util()
            output_rate = round(output_rate, 2)
        except AttributeError as e:
            input_rate, output_rate = "NA", "NA"
        try:
            if_index = adj["interface"].if_index
        except AttributeError as e:
            if_index = "NA"
        label = if_index + " R:" + str(output_rate) + "%" + " O:" + str(adj["metric"])
        return label

    def set_vs(self):

        source, target = self.neighbors()
        if self.reversed:
            source, target = target, source
            self.vs = {'from': source.uid_db(), 'to': target.uid_db(),

                       'label': self.l1,
                       'font': {'size': '8'},
                       'labelFrom': self.edge_label(orient='target'),
                       'labelTo': self.edge_label(orient='source'),
                       'smooth': {'type': 'curvedCW', 'roundness': self.roundness}}

        else:
            self.vs = {'from': source.uid_db(), 'to': target.uid_db(),
                       'label': self.l1,
                       'font': {'size': '8'},
                       'labelFrom': self.edge_label(orient='source'),
                       'labelTo': self.edge_label(orient='target'),
                       'smooth': {'type': 'curvedCW', 'roundness': self.roundness}}
        try:
            self.vs['ip_from'] = self.neighbors_dict[source.ip]['interface_ip']
        except Exception as e:
            self.dev.warning(f' error vs no ip source {e}')
            self.vs['ip_from'] = "NA"
        try:
            self.vs['ip_to'] = self.neighbors_dict[target.ip]['interface_ip']
        except Exception as e:
            self.dev.warning(f' error vs no ip target {e}')
            self.vs['ip_to'] = "NA"

        self.vs['color'] = {'color': self.color}
        try:
            self.vs['width'] = 2
            self.vs['interface_type'] = self.color
            self.vs['winterface_type'] = 3
        except Exception as e:
            pass
        try:
            self.vs['cusage'] = self.adj_neighbors['t']['interface'].color_usage[0]
            self.vs['wusage'] = self.adj_neighbors['t']['interface'].color_usage[1]
        except Exception as e:
            self.verbose.warning(f'ERROR color_usage {e}')
            try:

                self.vs['cusage'] = self.adj_neighbors['s']['interface'].color_usage[0]
                self.vs['wusage'] = self.adj_neighbors['s']['interface'].color_usage[1]
            except Exception as e:
                self.verbose.warning(f'ERROR color_usage {e}')
                self.vs['cusage'] = ospf_adjacency.__l1["DEF"]
                self.vs['wusage'] = 2

    @property
    def l1(self):
        try:
            l1_key = self.adj_ob[0]["interface"].l1_protocol_attr
        except AttributeError as e:
            try:
                l1_key = self.adj_ob[1]["interface"].l1_protocol_attr
            except:
                l1_key = "UNKNOWN"
        return l1_key

    @property
    def color(self):

        color = ospf_adjacency.__l1.get(self.l1, ospf_adjacency.__l1["DEF"]) if self.state == 'up' else \
            ospf_adjacency.__l1["DOWN"]

        self.dev.debug(f' {self.network_id} state {self.state} {color}')
        if self.state == 'down':
            self.verbose.warning(f' {self.network_id} state {self.state} {color}')
        return color

    def get_vs(self):
        return self.vs

    def adj_obj_list(self):
        neighbor_data = sorted([self.adj_neighbors["s"], self.adj_neighbors["t"]], key=lambda x: x["network_device"].ip)
        if self.reversed:
            reversed(neighbor_data)
        self.adj_ob = neighbor_data
        return neighbor_data

    def neighbors(self):
        if hasattr(self, 'adj_ob'):
            adj_list = self.adj_ob
        else:
            adj_list = self.adj_obj_list()
        return adj_list[0]["network_device"], adj_list[1]["network_device"]

    def pair_id(self):
        if not hasattr(self, 'pair'):
            source, target = self.neighbors()
            self.pair = "".join(sorted([source.ip, target.ip]))

        return self.pair

    @staticmethod
    def add_ospf_adjacency(list_networks, network_id, ospf_database, neighbors,
                           network_type, state='up'):
        try:
            list_networks.append(ospf_adjacency(network_id=network_id, ospf_database=ospf_database, neighbors=neighbors,
                                                network_type=network_type, state=state))
        except Exception as e:
            ospf_database.dev.warning(f'adding adjacency {network_id} error {e}')

    @property
    def sql_values(self):
        try:

            if self.adj_neighbors['s']['interface'] != 'null' and self.adj_neighbors['t']['interface'] != 'null':
                values = [self.network_id,
                          self.diagram_state.uid,
                          self.adj_neighbors['s']["router_id"],
                          self.adj_neighbors['s']['interface'].uid,
                          self.adj_neighbors['s']['metric'],
                          self.adj_neighbors['s']["interface_ip"],
                          self.adj_neighbors['t']["router_id"],
                          self.adj_neighbors['t']['interface'].uid,
                          self.adj_neighbors['t']['metric'],
                          self.adj_neighbors['t']["interface_ip"],
                          ]

                return "(" + (",".join([f"'{column}'" for column in values])) + ")"
            else:
                return ""
        except Exception as e:
            self.verbose.warning(
                f'sql_values {e} {self.adj_neighbors["s"]["interface"]} {self.adj_neighbors["t"]["interface"]}')
            return ""

    @staticmethod
    def sql_columns():

        return f'({",".join(ospf_adjacency.__columns__)})'

    def save(self):
        pass
