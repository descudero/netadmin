import ipaddress

from model.CiscoIOS import CiscoIOS

'''
Esta clase esta disenada para realizar procedimientos de rutas, mas que todo es para encontrar next hops. etc
    self.vrf ="null"
        self.protocol=""
        self.prefix="null"
        self.admin_distance=""
        self.protocol_metric=""
        self.protocol_type=""
        self.paths=[]
        self.protocol_as=""
        self.protocol="null"

        Se crea la clase vacia, pero se llena con los metodos estaticos:
        get_instance_route, este con una coneccion al equipo y un prefijo entra y genera un ruta.
        Por el momento solo funciona con cisco ios y cisco XR
'''


class IpRoute:
    def __init__(self):
        self.vrf = "null"
        self.protocol = ""
        self.prefix = "null"
        self.admin_distance = ""
        self.protocol_metric = ""
        self.protocol_type = ""
        self.paths = []
        self.protocol_as = ""

    '''
    Routing entry for 10.192.0.22/32
  Known via "ospf 14754", distance 110, metric 25, type inter area
  Last update from 10.192.38.217 on TenGigabitEthernet7/2, 2d18h ago
  Routing Descriptor Blocks:
  * 10.192.38.221, from 10.192.33.231, 2d18h ago, via TenGigabitEthernet1/2
      Route metric is 25, traffic share count is 1
    10.192.38.217, from 10.192.33.231, 2d18h ago, via TenGigabitEthernet7/2
      Route metric is 25, traffic share count is 1


Routing Table: ADMIN_DSLAM_ISLAS
Routing entry for 10.10.22.0/24
  Known via "bgp 14754", distance 200, metric 0, type internal
  Last update from 10.192.33.8 4w1d ago
  Routing Descriptor Blocks:
  * 10.192.33.8 (default), from 10.192.35.108, 4w1d ago
      Route metric is 0, traffic share count is 1
      AS Hops 0
      MPLS label: 1521
      MPLS Flags: MPLS Required, NSF
    '''

    @staticmethod
    def get_instance_route(connection, parent_device, prefix, vrf="null"):
        route = "null"
        show_route_output = IpRoute.get_show_ip_route(connection, parent_device, prefix, vrf)
        if (parent_device.platform == "CiscoIOS"):
            route = IpRoute.parse_route_ios(show_route_output)
        else:
            route = IpRoute.parse_route_xr(show_route_output)
        return route

    @staticmethod
    def parse_route_ios(input_show):
        ip_route = IpRoute()
        has_vrf = (input_show.find("Routing Table:") > -1)
        # print("has vrf" + str(has_vrf))
        lines = input_show.split("\n")
        lines.reverse()
        # print(lines)

        if has_vrf:
            # print(lines)
            # print("made pop vrf")
            lines.pop()
            ip_route.vrf = lines.pop().replace("Routing Table: ", "")
            # print(lines)
        # print("made pop route")
        # print(lines)
        route_line = lines.pop().replace("Routing entry for ", "").replace(", supernet", "")

        # print(route_line)
        ip_route.prefix = ipaddress.ip_network(route_line)
        # print("made pop protocol")
        split_protocol_line = lines.pop().split(",")
        known_via_split = split_protocol_line[0].replace("  Known via \"", "").replace("\"", "").split(" ")
        ip_route.protocol = known_via_split[0]
        if (len(known_via_split) > 1):
            ip_route.protocol_as = known_via_split[1]
        ip_route.admin_distance = split_protocol_line[1].replace(" distance ", "replace")
        ip_route.protocol_metric = split_protocol_line[2].replace(" metric ", "").split(" ")[0]
        if len(split_protocol_line) > 3:
            ip_route.protocol_type = split_protocol_line[3]
        split_paths = input_show.split("  Routing Descriptor Blocks:\n")[1].split("\n")
        paths = []
        for index, line in enumerate(split_paths):
            if (line.find("from") > -1):
                path = {"next_hop": "0.0.0.0", "originator": "0.0.0.0", "time": "0", "out_interface": "recursive"}
                route_info = line.split(",")
                path["next_hop"] = route_info[0].replace(" ", "").replace("*", "")

                path["originator"] = route_info[1].replace(" ", "").replace("from", "")
                path["time"] = route_info[2].replace(" ", "").replace("ago", "")
                if (len(route_info) > 3):
                    path["out_interface"] = CiscoIOS.get_normalize_interface_name(
                        route_info[3].replace(" ", "").replace("via", ""))

                if (path["next_hop"].find("(default)") > -1):
                    path["out_interface"] = "recusive_default"
                    path["next_hop"] = path["next_hop"].replace("(default)", "")
                # print(route_info)
                paths.append(path)
        ip_route.paths = paths
        return ip_route

    @staticmethod
    def get_show_ip_route(connection, parent_device, prefix, vrf="null", command=" show ip route"):
        command += "" if vrf == "null" else " vrf " + vrf
        command += " " + prefix
        output = parent_device.send_command(connection=connection, command=command)
        return output

    def get_string_route(self):

        output = " network " + str(self.prefix) + "\n"
        for next_hop in self.paths:
            output += " next hop " + next_hop["next_hop"] + " " + next_hop["out_interface"] + "\n"

        return output

    def __str__(self):
        output = " network " + str(self.prefix) + "\t"
        for next_hop in self.paths:
            output += " next hop " + next_hop["next_hop"] + " " + self.interface + "\t"
        return output

    def __repr__(self):
        return "IpRoute p" + str(self.prefix)

    @staticmethod
    def parse_route_xr(input_show, vrf="null"):
        '''RP/0/RP0/CPU0:GNCYGTG2N2D4B07A02FWT1#show route 10.1.5.64
Mon Feb 26 13:43:17.769 GMT

Routing entry for 10.1.5.64/30
  Known via "ospf 14754", distance 110, metric 20, type extern 2
  Installed Feb 26 11:27:48.070 for 02:15:29
  Routing Descriptor Blocks
    10.192.16.153, from 10.192.129.114, via HundredGigE0/1/0/0
      Route metric is 20
    10.192.47.46, from 10.192.129.114, via HundredGigE0/5/0/0
      Route metric is 20
  No advertising protos.


  RP/0/RSP0/CPU0:HHERCRMPN1T1FFM4#show route vrf CR_TELEPRESENCE 10.1.63.112
Mon Feb 26 13:44:48.382 GMT

Routing entry for 10.1.63.112/29
  Known via "bgp 14754", distance 200, metric 0, type internal
  Installed Feb 23 02:17:20.264 for 3d11h
  Routing Descriptor Blocks
    10.192.129.19, from 10.192.9.30
      Nexthop in Vrf: "default", Table: "default", IPv4 Unicast, Table Id: 0xe0000000
      Route metric is 0
  No advertising protos.

    '''

        ip_route = IpRoute()
        lines = input_show.split("\n")
        lines.reverse()
        lines.pop()
        lines.pop()
        route_line = lines.pop().replace("Routing entry for ", "").replace(", supernet", "")
        ip_route.prefix = ipaddress.ip_network(route_line)
        split_protocol_line = lines.pop().split(",")
        known_via_split = split_protocol_line[0].replace("  Known via \"", "").replace("\"", "").split(" ")
        ip_route.protocol = known_via_split[0]
        if (len(known_via_split) > 1):
            ip_route.protocol_as = known_via_split[1]
        ip_route.admin_distance = split_protocol_line[1].replace(" distance ", "replace")
        ip_route.protocol_metric = split_protocol_line[2].replace(" metric ", "").split(" ")[0]
        if len(split_protocol_line) > 3:
            ip_route.protocol_type = split_protocol_line[3]
        split_paths = input_show.split("  Routing Descriptor Blocks\n")[1].split("\n")
        paths = []
        for index, line in enumerate(split_paths):
            if (line.find("from") > -1):
                path = {"next_hop": "0.0.0.0", "originator": "0.0.0.0", "time": "0", "out_interface": "recursive"}
                route_info = line.split(",")
                path["next_hop"] = route_info[0].replace(" ", "").replace("*", "")

                path["originator"] = route_info[1].replace(" ", "").replace("from", "")
                path["time"] = "xr"
                if (len(route_info) > 2):
                    path["out_interface"] = CiscoIOS.get_normalize_interface_name(
                        route_info[2].replace(" ", "").replace("via", ""))

                if (path["next_hop"].find("(default)") > -1):
                    path["out_interface"] = "recusive_default"
                    path["next_hop"] = path["next_hop"].replace("(default)", "")

                paths.append(path)
        ip_route.paths = paths

        return ip_route

    def has_paths(self):
        '''

        :return: si tiene paths la ruta
        '''
        return len(self.paths) > 0
