import lib.pyyed as pyyed
from colour import Color


class ospf_adjacency:
    def __init__(self, network_id, ospf_database, neighbors, network_type='p2p'):
        self.network_id = network_id
        self.network_type = network_type
        self.ospf_database = ospf_database
        self.adj_neighbors = {}
        for neighbor in neighbors:
            neighbor_key = "s"
            if 's' in self.adj_neighbors:
                neighbor_key = 't'
            device = self.ospf_database.routers[neighbor["router_id"]]

            self.adj_neighbors[neighbor_key] = neighbor
            try:
                self.adj_neighbors[neighbor_key]["interface"] = device.interfaces_ip[neighbor["interface_ip"]]
            except KeyError:
                print(len(device.interfaces_ip.keys()), str(neighbor["interface_ip"] in device.interfaces_ip))
                print("not interface found ", device, " ", neighbor["interface_ip"])
                self.adj_neighbors[neighbor_key]["interface"] = "null"
            self.adj_neighbors[neighbor_key]["network_device"] = device
        # self.adj_neighbors["s"]["network_device"].add_p2p_ospf(self,self.adj_neighbors["t"])
        # self.adj_neighbors["t"]["network_device"].add_p2p_ospf(self,self.adj_neighbors["s"])

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
