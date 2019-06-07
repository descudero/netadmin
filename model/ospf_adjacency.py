import lib.pyyed as pyyed
from colour import Color
from tools import logged
import os
import shelve
from pprint import pprint
from model.InterfaceUfinet import InterfaceUfinet
import threading


@logged
class ospf_adjacency:
    __l1 = {"MAYA": "#228B22",
            "LEVEL3": "#FF00FF",
            "CENTURY": "#FF1493",
            "TELXIUS": "#8B4513",
            "LANAUTILUS": "#BC8F8F",
            "DEF": "#00BFFF", "DOWN": "#330F53"

            }

    __columns__ = ['network_id',
                   'diagram_state_uid',
                   'net_device_1_ip',
                   'interface_1_uid',
                   'interface_1_weight',
                   'interface_1_ip',
                   'net_device_2_ip',
                   'interface_2_uid',
                   'interface_2_weight',
                   'interface_2_ip']

    __table__ = "diagram_state_adjacencies"

    def __init__(self, lock, network_id, ospf_database, neighbors, network_type='p2p', state='up'):
        # interfaces_data = ['172.20.33.86',
        #                    '172.20.33.101',
        #                    '172.20.33.74',
        #                    '172.20.33.73',
        #                    '172.20.33.53',
        #                    '172.20.33.85',
        #                    '172.20.33.82']

        self.uid = 0
        self.diagram_state = None
        self.dev.debug("net " + network_id + " start init ")
        self.network_id = network_id
        self.network_type = network_type
        self.ospf_database = ospf_database
        self.adj_neighbors = {}
        self.reversed = False
        self.neighbors_dict = {neighbor["router_id"]: neighbor for neighbor in neighbors}

        self.s = neighbors[0]
        self.t = neighbors[1]
        self.s_device = self.ospf_database.routers[self.s["router_id"]]
        self.t_device = self.ospf_database.routers[self.t["router_id"]]
        # if self.s["interface_ip"] in interfaces_data or self.t["interface_ip"] in interfaces_data:
        #     self.verbose.warning(
        #         f"__INIT__ Debug  {self.s_device.ip} {self.s_device.hostname} {self.s['router_id']}  ")
        self.s["network_device"] = self.s_device
        self.t["network_device"] = self.t_device
        try:
            self.s_interface = self.s_device.interfaces_ip[self.s["interface_ip"]]
            # if "BDI" in self.s_interface.if_index or "Po" in self.s_interface.if_index:
            #     self.verbose.warning(
            #         f"__INIT__ d{self.s_device.ip} {self.s_device.hostname}  i{self.s_interface.if_index}")
        except KeyError:
            self.s_interface = "null"
            self.verbose.warning(
                f'_INIT_ no interface ip uid:{self.s_device.uid} N:{self.network_id} '
                f'dev:{self.s_device.hostname} I:{self.s["interface_ip"]}')
        try:
            self.t_interface = self.t_device.interfaces_ip[self.t["interface_ip"]]
            # if "BDI" in self.t_interface.if_index or "Po" in self.t_interface.if_index:
            #     self.verbose.warning(
            #         f"__INIT__ d{self.t_device.ip} {self.t_device.hostname}  i{self.t_interface.if_index}")
        except KeyError:
            self.t_interface = "null"

            self.verbose.warning(
                f'_INIT_ no interface ip uid:{self.t_device.uid} N:{self.network_id}'
                f' dev:{self.t_device.hostname} I:{self.t["interface_ip"]}')
        self.s["interface"] = self.s_interface
        self.t["interface"] = self.t_interface
        try:
            setattr(self, f's_ip', self.s_interface.ip)
        except Exception as e:
            self.dev.warning(f'__init__  no ip s_ip')
        try:
            setattr(self, f't_ip', self.t_interface.ip)
        except Exception as e:
            self.dev.warning(f'__init__  no ip t_ip')
        # if "BD" in self.s_interface.if_index or "Port" in self.s_interface.if_index:
        #     self.verbose.warning(f'N:{self.network_id} {self.s_device.ip} {self.s_interface}')
        # if "BD" in self.t_interface.if_index or "Port" in self.t_interface.if_index:
        #     self.verbose.warning(f'N:{self.network_id} {self.t_device.ip} {self.t_interface}')
        pair = self.pair_id()

        with lock:
            try:
                self.ospf_database.neighbors_occurrences_count[pair] += 1

            except Exception as  e:

                self.dev.warning(f'ERROR_INIT_ neighbors_occurrences_count counter {e}')
        try:
            self.roundness = self.ospf_database.edge_roundness[self.ospf_database.neighbors_occurrences_count[pair]]
        except Exception as e:
            self.dev.warning(f'ERROR_INIT_ roundess {e}')

        if self.ospf_database.neighbors_occurrences_count[pair] % 2 == 0:
            self.reversed = True
            self.adj_obj_list()
            self.dev.debug(" net_id reversed ")
        else:
            self.dev.debug(" net_id not reversed ")
        # self.adj_neighbors["s"]["network_device"].add_p2p_ospf(self,self.adj_neighbors["t"])
        # self.adj_neighbors["t"]["network_device"].add_p2p_ospf(self,self.adj_neighbors["s"])
        self.dev.debug(f"adjacency {self.network_id} inited")
        self.set_vs()

    @property
    def state(self):

        return "up" if self.up else "down"

    @property
    def up(self):
        try:
            return self.s_interface.up and self.t_interface.up
        except:
            return False

    def __repr__(self):
        return str(self.__class__) + " NET " + self.network_id + " " + self.network_type + " N "

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
        self.dev.debug(f'{self.pair} init set vs')
        source, target = self.neighbors()
        if self.reversed:
            source, target = target, source
            self.vs = {'from': source.uid, 'to': target.uid,

                       'label': self.l1,
                       'font': {'size': '8'},
                       'labelFrom': self.edge_label(orient='target'),
                       'labelTo': self.edge_label(orient='source'),
                       'smooth': {'type': 'curvedCW', 'roundness': self.roundness}}

        else:
            self.vs = {'from': source.uid, 'to': target.uid,
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

        try:

            self.vs['interface_type'] = self.color
            if self.up:
                self.vs['width'] = 2
                self.vs['winterface_type'] = 3
            else:
                self.vs['width'] = 5
                self.vs['winterface_type'] = 5
        except Exception as e:
            pass
        try:
            color, width = InterfaceUfinet.maximum_usage_color(self.s_interface
                                                               , self.t_interface)
            self.vs['color'] = {'color': color}

            self.vs['cusage'] = color
            self.vs['wusage'] = width
        except Exception as e:
            self.dev.warning(f'ERROR color_usage {e}')
            self.vs['cusage'] = ospf_adjacency.__l1["DEF"]
            self.vs['color'] = {'color': ospf_adjacency.__l1["DEF"]}
            self.vs['width'] = 5
            self.vs['wusage'] = 2
        self.dev.debug(f'{self.network_id} end set vs')

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

        color = ospf_adjacency.__l1.get(self.l1, ospf_adjacency.__l1["DEF"]) if self.up else \
            ospf_adjacency.__l1["DOWN"]
        self.dev.debug(f' {self.network_id} state {self.state} {color}')

        return color

    def get_vs(self):
        return self.vs

    def adj_obj_list(self):
        if not hasattr(self, "adj_ob"):
            neighbor_data = [self.t, self.s] if self.s["network_device"].ip > self.t["network_device"].ip else [self.t,
                                                                                                                self.s]
            if self.reversed:
                reversed(neighbor_data)
            self.adj_ob = neighbor_data
        return self.adj_ob

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
    def add_ospf_adjacency(lock, list_networks, network_id, ospf_database, neighbors,
                           network_type, state='up'):
        try:
            adj = ospf_adjacency(lock, network_id=network_id, ospf_database=ospf_database, neighbors=neighbors,
                                 network_type=network_type, state=state)

            with lock:
                list_networks.append(adj)
        except Exception as e:
            ospf_database.verbose.warning(f'adding adjacency {network_id} ERROR {e} {e.__class__}')

    @property
    def sql_values(self):
        try:

            if self.s_interface != 'null' and self.t_interface != 'null':
                if self.s_interface.uid != 0 and self.t_interface.uid != 0:
                    values = [self.network_id,
                              self.diagram_state.uid,
                              self.s["router_id"],
                              self.s_interface.uid,
                              self.s['metric'],
                              self.s["interface_ip"],
                              self.t["router_id"],
                              self.t_interface.uid,
                              self.t['metric'],
                              self.t["interface_ip"],
                              ]

                    return "(" + (",".join([f"'{column}'" for column in values])) + ")"
                else:
                    return ""

            else:
                return ""
        except Exception as e:
            self.dev.warning(
                f'sql_values {e} {self.s_interface} {self.t_interface}')
            return ""

    @staticmethod
    def sql_columns():

        return f'({",".join(ospf_adjacency.__columns__)})'

    def save(self):
        pass
