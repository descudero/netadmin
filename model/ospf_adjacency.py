import lib.pyyed as pyyed
from colour import Color
from tools import logged


@logged
class ospf_adjacency:
    __l1 = {"CABLE_MAYA": "#228B22",
            "LEVEL3": "#FF00FF",
            "CENTURY": "#FF1493",
            "TELXIUS": "#8B4513", "LANAUTILUS": "#BC8F8F", "DEF": "#00BFFF"

            }

    def __init__(self, network_id, ospf_database, neighbors, network_type='p2p'):
        self.verbose.info("net " + network_id + " start init ")
        self.network_id = network_id
        self.network_type = network_type
        self.ospf_database = ospf_database
        self.adj_neighbors = {}
        self.reversed = False
        for neighbor in neighbors:
            neighbor_key = "s"
            if 's' in self.adj_neighbors:
                neighbor_key = 't'
            device = self.ospf_database.routers[neighbor["router_id"]]

            self.adj_neighbors[neighbor_key] = neighbor
            try:
                self.adj_neighbors[neighbor_key]["interface"] = device.interfaces_ip[neighbor["interface_ip"]]
            except KeyError:
                self.adj_neighbors[neighbor_key]["interface"] = "null"
            self.adj_neighbors[neighbor_key]["network_device"] = device
        pair = self.pair_id()

        self.ospf_database.neighbors_occurrences_count[pair] += 1
        self.roundness = self.ospf_database.edge_roundness[self.ospf_database.neighbors_occurrences_count[pair]]
        if self.ospf_database.neighbors_occurrences_count[pair] % 2 == 0:
            self.reversed = True
            self.adj_obj_list()
            self.verbose.critical(" net_id reversed ")
        else:
            self.verbose.critical(" net_id not reversed ")
        # self.adj_neighbors["s"]["network_device"].add_p2p_ospf(self,self.adj_neighbors["t"])
        # self.adj_neighbors["t"]["network_device"].add_p2p_ospf(self,self.adj_neighbors["s"])
        self.dev.info("adjacency " + pair + " inited")
        self.set_vs()

    def __repr__(self):
        return str(self.__class__) + " NET " + self.network_id + " " + self.network_type + " N " + str(
            len(self.adj_neighbors))

    def yed_edge(self):
        green = Color("LawnGreen")
        yellow = Color("Yellow")
        red = Color("Red")
        colors = list(green.range_to(yellow, 50)) + list(yellow.range_to(red, 51))
        additional_labels = []
        line_type = "line"
        if "NAP" in self.adj_neighbors["s"]["network_device"].hostname or \
                "NAP" in self.adj_neighbors["t"]["network_device"].hostname:
            line_type = "dashed"
        sd = self.adj_neighbors["s"]["network_device"]
        td = self.adj_neighbors["t"]["network_device"]
        tx, ty, sx, sy = td.x, sd.y, sd.x, sd.y

        t_dir = td.get_xy_direction(sx, sy)
        s_dir = sd.get_xy_direction(sx, sy)

        etx, ety = td.get_next_edge_point(sx, sy)
        esx, esy = sd.get_next_edge_point(tx, ty)
        for key, neighbor in self.adj_neighbors.items():
            input_rate, output_rate = neighbor["interface"].util()
            color = colors[int(max(input_rate, output_rate))].hex
            width = str(2 * int(max(input_rate, output_rate) / 10))
            interface_rate_text = neighbor["interface"].if_index + "C:" + neighbor[
                "metric"] + '\n' + str(output_rate) + "% "
            additional_labels.append(
                {"text": interface_rate_text, "color": "#000000", "position": key + "center", "size": '20'})

        additional_labels.append({"text": self.network_id,
                                  "color": "#000000", "position": "center", "size": '20'})

        edge = pyyed.Edge(node1=self.adj_neighbors['s']["router_id"],
                          node2=self.adj_neighbors['t']["router_id"],
                          id=self.network_id, line_type=line_type,
                          additional_labels=additional_labels, width=width,
                          color=color, sy=esy, sx=esx, tx=etx, ty=ety
                          )

        return edge

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
        green = Color("LawnGreen")
        yellow = Color("Yellow")
        red = Color("Red")
        source, target = self.neighbors()
        if self.reversed:
            source, target = target, source
            self.vs = {"color": self.color(), 'from': source.uid_db(), 'to': target.uid_db(),
                       'label': '-',
                       'font': {'size': '8'},
                       'labelFrom': self.edge_label(orient='target'),
                       'labelTo': self.edge_label(orient='source'),
                       'smooth': {'type': 'curvedCW', 'roundness': self.roundness}}
        else:
            self.vs = {"color": self.color(), 'from': source.uid_db(), 'to': target.uid_db(),
                       'label': '-',
                       'font': {'size': '8'},
                       'labelFrom': self.edge_label(orient='source'),
                       'labelTo': self.edge_label(orient='target'),
                       'smooth': {'type': 'curvedCW', 'roundness': self.roundness}}

    def color(self):
        l1_key = ""
        try:
            l1_a_key = self.adj_ob[0]["interface"].l1_protocol_attr
        except AttributeError as e:
            l1_a_key = "UNKNOWN"
        try:
            l1_b_key = self.adj_ob[1]["interface"].l1_protocol_attr
        except AttributeError as e:
            l1_b_key = "UNKNOWN"

        if l1_a_key != "UNKNOWN":
            l1_key = l1_a_key
        elif l1_b_key != "UNKNOWN":
            l1_key = l1_b_key

        if l1_key in ospf_adjacency.__l1:
            self.verbose.info(l1_a_key)
            self.verbose.info(l1_b_key)
            _color = ospf_adjacency.__l1[l1_key]
            self.verbose.info(_color)
        else:
            _color = ospf_adjacency.__l1["DEF"]
        return ospf_adjacency.__l1.get(l1_key, ospf_adjacency.__l1["DEF"])

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


def add_ospf_adjacency(list_networks, network_id, ospf_database, neighbors,
                       network_type):
    list_networks.append(ospf_adjacency(network_id=network_id, ospf_database=ospf_database, neighbors=neighbors,
                                        network_type=network_type))
