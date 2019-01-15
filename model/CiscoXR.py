import re

from model.CiscoIOS import CiscoIOS as Parent
from model.Interface import InternetInterface
from model.InterfaceIOS import InterfaceIOS
from model.RoutePolicy import RoutePolicy
from model.prefixSet import PrefixSet
from pprint import pprint
from tools import normalize_interface_name, logged

# from kivy.uix.boxlayout import bgpBoxLayout
# from LabelB import LabelB

@logged
class CiscoXR(Parent):

    def set_config(self):
        # los asr no tienenconfig solo running config
        return self.setActualConfig()

    def set_arp_list(self, vrf="default"):
        command = "show  arp "
        command += (" vrf " + vrf + " ") if vrf != "default" else " "
        command += "  | I ARPA"

        connection = self.connect()
        output = self.send_command(connection=connection, command=command)

        list_arp_entries = {}
        for line in output.split("\n")[1:]:
            arp_info = {"ip": "0.0.0.0", "time": "-", "mac": "0000.0000.0000", "source": "Interface",
                        "interface": "null"}
            splitline = re.sub(" +", " ", line).split(" ")
            arp_info["ip"] = splitline[0]
            arp_info["time"] = splitline[1]
            arp_info["mac"] = splitline[2]
            arp_info["source"] = splitline[3]
            arp_info["interface"] = splitline[5]
            list_arp_entries[arp_info["ip"]] = arp_info
        self.arp_list = list_arp_entries
        return self.arp_list

    def set_static_route(self):

        connection = self.connect()
        output = self.send_command(connection=connection,
                                   command="show running-config formal router static ",
                                   timeout=5)

        lineas_config = output.split("\n")
        self.static_routes = {}
        for index, linea in enumerate(lineas_config):
            ad = "1"  # distancia administrativa inicial
            linea = linea.replace("\n", "")
            linea_split = linea.split(" ")
            # print(linea_split)
            if (len(linea_split) > 6 and linea.startswith("router static")):
                i_route = 5;
                i_mask = 5;
                i_next_hop = 6
                i_ad = 7
                route_global = True;
                if (linea.startswith("router static vrf")):
                    i_route = 7;
                    i_mask = 7;
                    i_next_hop = 8
                    i_ad = 9
                    vrf = linea_split[3]
                    route_global = False
                else:
                    vrf = "null"

                next_hop = linea_split[i_next_hop]
                pat = re.compile("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}")
                test = pat.match(next_hop)

                if (test):
                    if (len(linea_split) > i_ad + 1):
                        if (linea_split[i_next_hop + 1].isdigit()):
                            ad = linea_split[i_ad]
                else:
                    if (len(linea_split) > i_next_hop + 1):
                        next_hop = linea_split[i_next_hop + 1]
                        if (len(linea_split) > i_ad + 1):
                            if (linea_split[i_ad].isdigit()):
                                ad = linea_split[i_ad + 1]
                    else:
                        next_hop = "null"
                if next_hop != "null":
                    route = linea_split[i_route].split("/")[0]
                    mask = linea_split[i_mask].split("/")[1]
                self.static_routes[route + next_hop + vrf] = {"global": route_global,
                                                              "vrf": vrf,
                                                              "route": route,
                                                              "mask": mask,
                                                              "next_hop": next_hop,
                                                              "ad": ad,
                                                              "linea": linea}
        return self.static_routes

    def set_internet_interfaces(self):
        if not hasattr(self, "config"):
            self.set_config()
        if not hasattr(self, "internet_interfaces"):
            lines = self.config.split("\n")
            interfaces = {};
            for index, line in enumerate(lines):
                if line.startswith("interface"):
                    if index + 1 < len(lines):
                        if lines[index + 1].startswith(" description"):
                            if lines[index + 1].find("PEER:") != -1:
                                # description TAG:ROJO ! CP:40GB ! EBGP:COGENT ! PEER:38.88.165.53 !
                                #  EBGPID:CIRCUIT-ID 1-300032199 ! TX:AMX ! TXID:CABLE AMX-1 -REMOTE EQ ROUTER
                                # 21.MIA03 ID-AMX IAM1GTIZPPBR-USFLMNAP-GE10-005
                                description = lines[index + 1].replace(" description", "").replace("\n", "")
                                data = description.split("!")
                                tag = data[0].replace("TAG:", "").replace(" ", "")
                                capacidad = data[1].replace("CP:", "").replace(" ", "")
                                ebgp = data[2].replace("EBGP:", "").replace(" ", "")
                                peer = data[3].replace("PEER:", "").replace(" ", "")
                                ebgpid = data[4].replace("EBGPID:", "").replace(" ", "")
                                tx = data[5].replace("TX:", "").replace(" ", "")
                                # txid = data[6].replace("TXID:", "")
                                interface_index = line.replace("interface ", "").replace(" ", "").replace("\n", "")
                                interface = InternetInterface(interface_index, description, tag, peer, ebgp, ebgpid, tx,
                                                              "")
                                interfaces[interface_index] = interface
            self.internet_interfaces = interfaces

    def set_route_policy(self):
        if not hasattr(self, "config"):
            self.set_config()
        if not hasattr(self, "prefix_sets"):
            self.set_prefix_set()
        lines = self.config.split("\n")
        route_maps = {}
        index = 0
        in_policy = False
        policy = RoutePolicy("inicial", self)
        for index in range(0, len(lines)):

            if lines[index].startswith("route-policy"):
                name_policy = lines[index].replace("route-policy ", "").replace("\n", "")
                in_policy = True
                policy = RoutePolicy(name_policy, self)
            else:
                if in_policy:
                    if lines[index].startswith("  if") or \
                            lines[index].startswith("  elseif"):
                        condition_policy = lines[index].replace("  if ", "") \
                            .replace(" then", "") \
                            .replace("  elseif ", "") \
                            .replace("\n", "")

                        if (lines[index + 1].startswith("    drop")
                                or lines[index + 1].startswith("    pass")
                                or lines[index + 1].startswith("    prepend")
                                or lines[index + 1].startswith("    apply")):
                            action_policy = lines[index + 1].replace("\n", "").replace("    ", "")
                            policy.setSequence(condition_policy, action_policy)
                    else:
                        if lines[index].startswith("  endif"):
                            in_policy = False
                            route_maps[policy.name] = policy
        self.route_policies = route_maps

    def set_prefix_set(self):
        if not hasattr(self, "config"):
            self.set_config()

        lines = self.config.split("\n")
        prefix_sets = {}

        in_prefix = False
        prefix_set = PrefixSet("inicial")
        for index in range(0, len(lines)):
            if in_prefix:
                if lines[index].find("#") == -1:
                    if lines[index].find("end-set") != -1:
                        in_prefix = False
                        prefix_sets[prefix_set.name] = prefix_set
                    else:
                        prefix_set.setSequence(lines[index].replace("  ", "").replace(",", "").replace("\n", ""))

            else:
                if lines[index].startswith("prefix-set"):
                    prefix_set = PrefixSet(lines[index].replace("prefix-set ", "").replace("\n", ""))
                    in_prefix = True

        self.prefix_sets = prefix_sets

    def routes(self, address_family=" ipv4 unicast", vrf="INTERNET", type="all"):
        pass

    def route_policy_per_interface(self):
        self.set_internet_interfaces()
        self.set_route_policy()
        policy_interface = {}

        # print(self.internet_interfaces)
        for key, interface in self.internet_interfaces.items():

            name_policy = self.search_name_route_policy(interface.peer.replace(".", "_"))
            policy = self.route_policies[name_policy]
            if policy.hasApply() != 0:
                name_policy = policy.hasApply()
            policy_interface[key] = self.route_policies[name_policy];
        return policy_interface

    def search_name_route_policy(self, contains):
        # print(contains)
        # print(self.route_policies.items())
        match = ""
        for key, policy in self.route_policies.items():
            if key.find(contains) != -1 and key.find("out") != -1:
                return key
        # print(self.ip)
        return False

    def print_prefix(self):
        result = ""
        for key, prefix in self.prefix_sets.items():
            result += prefix.printTable()
        return result

    def get_policy_map_interface_rate(self, direction="all"):
        if not hasattr(self, "internet_interfaces"):
            self.set_internet_interfaces()
        map_policy = {}
        connection = self.connect()
        for index, interface in self.internet_interfaces.items():
            map_policy[index] = interface.get_service_policy_rate(connection=connection,
                                                                  parentDevice=self)
        return map_policy

    def get_summarize_rate(self, map_policy="", filter_tag=""):
        if map_policy == "":
            map_policy = self.get_policy_map_interface_rate()
        summary_map = {"in": {}, "out": {}}
        directions = ["in", "out"]
        actions = ["transmited", "match", "dropped"]

        for direction in directions:
            for index_interface, interface in map_policy.items():

                if direction in interface:
                    for class_name, class_values in interface[direction].items():
                        if class_name not in summary_map[direction]:
                            summary_map[direction][class_name] = {"transmited": 0, "match": 0, "dropped": 0}
                        for action in actions:
                            summary_map[direction][class_name][action] += class_values[action]

        for direction in directions:
            for action in actions:
                summary_map[direction]["%"][action] = \
                    summary_map[direction]["total"][action] / \
                    summary_map[direction]["bw"][action]

        return summary_map

    def print_policy_map_rate_distribution(self, results=[], printit=True):

        interfaces_qos_rate = self.get_policy_map_interface_rate()
        summary_rate = self.get_summarize_rate(interfaces_qos_rate)
        output = "IPP|Interfaz|TAG|"

        for name_direction, classes_qos in summary_rate.items():
            output += "direction|"
            for class_name, data in classes_qos.items():
                output += class_name.replace("ENTRADAINTERNET", "").replace("SALIDAINTERNET", "") + "|"
        output += "\n"

        for interface, direction in interfaces_qos_rate.items():
            output += self.display_name + "|" + interface + "|" + self.internet_interfaces[interface].tag + "|"

            for name_direction, classes_qos in direction.items():
                output += name_direction + "|"

                for class_name, data in summary_rate[name_direction].items():
                    if class_name in classes_qos:
                        output += str(round(classes_qos[class_name]["transmited"], 2)) + "|"

            output += "\n"

        output += self.display_name + "|Total|" + self.display_name + "|"
        for name_direction, classes_qos in summary_rate.items():
            output += name_direction + "|"
            for class_name, data in classes_qos.items():
                output += str(round(data["transmited"], 2)) + "|"
        if printit:
            print(output)
        results.append(output)
        return output + "\n";

    def ip_address_in_bgp_out_policy(self, ip, filter=["pass"]):
        policies = {}
        route_policies = self.route_policy_per_interface()

        for name_route, routePolicy in route_policies.items():
            prefixsets = routePolicy.ipInSequence(ip=ip, filter=filter)
            if len(prefixsets) > 0:
                policies[name_route] = {"policy": routePolicy, "name": routePolicy.name, "prefixsets": prefixsets}

        return policies

    def set_internet_interfaces_stats(self):
        if not hasattr(self, "internet_interfaces"):
            self.set_internet_interfaces()
        connection = self.connect()
        for index, interface in self.internet_interfaces.items():
            interface.set_interface_stats(connection=connection, parentDevice=self)
        self.interfaces_stats_set = True

    def get_interfaces_rate_in(self, check_stats=False):
        if check_stats or not self.interfaces_stats_set:
            self.set_interfaces_stats()
        data_rate = {}
        for index, interface in self.internet_interfaces.items():
            data_rate[index] = getattr(interface, "bandwith")
        return data_rate

    def set_conected_routes(self, vrf="default"):
        command = "show route "
        command += " vrf " + vrf + " " if vrf != "default" else " "
        command += " connected | i C"
        self.connected_routes = {}
        connection = self.connect()
        output = self.send_command(connection=connection, command=command)

        for line in output.split("\n")[1:]:
            split_line = line.replace("C    ", "").replace(" is directly connected", "").split(',')

            self.connected_routes[split_line[0]] = split_line[2]

    def set_ip_bgp_neighbors(self, address_family="ipv4 unicast"):
        if not hasattr(self, "bgp_neighbors"):
            self.bgp_neighbors = {}

        connection = self.connect()
        command = "show bgp " + address_family + " neighbors"
        show_bgp_neighbors = self.send_command(connection, command, self.hostname, timeout=5)
        # print(show_bgp_neighbors)
        neighbor_string_split = show_bgp_neighbors.split("BGP neighbor is ")
        for neighbor_string in neighbor_string_split:
            if (neighbor_string.find('Remote AS ') > 0):
                bgp_session = {"bgp_neighbor_ip": "0.0.0.0",
                               "bgp_remote_as": 0, "bgp_session_type": 0,
                               "bgp_state": 0,
                               "bgp_time_in_state": 0,
                               "bgp_address_family": "",
                               "bgp_total_prefixes_advertised": 0,
                               "bgp_accepted_prefixes": 0,
                               "bgp_policy_out": "NA",
                               "bgp_policy_in": "NA"
                               }

                lines_neighbor = neighbor_string.split("\n")
                if (lines_neighbor[0].find("vrf") > 0):
                    bgp_session["bgp_neighbor_ip"] = lines_neighbor[0].split("vrf")[0].replace(",", "")
                else:
                    bgp_session["bgp_neighbor_ip"] = lines_neighbor[0].replace(" ", "")
                for line in lines_neighbor:

                    if (line.find("For Address Family: ") > 0 and bgp_session["bgp_address_family"] == ""):
                        bgp_session["bgp_address_family"] = line.replace("For Address Family: ", "")
                    if (line.find("Prefix advertised ") > 0 and bgp_session["bgp_address_family"] != ""):
                        bgp_session["bgp_total_prefixes_advertised"] = int(
                            line.split(",")[0].replace("Prefix advertised ", ""))
                    if (line.find("accepted prefixes, ") > 0 and bgp_session["bgp_address_family"] != ""):
                        bgp_session["bgp_accepted_prefixes"] = int(
                            line.split(",")[0].replace("accepted prefixes", ""))
                    if (line.find("Policy for incoming advertisements is ") > 0 and bgp_session[
                        "bgp_address_family"] != ""):
                        bgp_session["bgp_policy_in"] = line.replace("Policy for incoming advertisements is ", "")
                    if (line.find("Policy for outgoing advertisements is ") > 0 and bgp_session[
                        "bgp_address_family"] != ""):
                        bgp_session["bgp_policy_out"] = line.replace("Policy for outgoing advertisements is ", "")

                    if (line.find("Remote AS") > 0):
                        line_split = line.split(",")
                        bgp_session["bgp_remote_as"] = line_split[0].replace(" Remote AS ", "")
                        if (bgp_session["bgp_remote_as"].find("vrf") > 0):
                            bgp_session["bgp_remote_as"] = line_split[2].replace(" Remote AS ", "")
                            bgp_session["bgp_vrf"] = line_split[1].replace("vrf", "").replace(" ", "")
                            bgp_session["bgp_session_type"] = line_split[4].replace("", "")
                        else:
                            bgp_session["bgp_session_type"] = line_split[2]
                    if (line.find("Description:") > 0):
                        bgp_session["bgp_description"] = line.replace("Description:", "").replace(" ", "")
                    if (line.find("BGP state") > 0):
                        line_split = line.replace("BGP state = ", "").split(",")
                        bgp_session["bgp_state"] = line_split[0].replace(" ", "")
                        if (len(line_split) > 1):
                            bgp_session["time_in_state"] = line_split[1].replace(" up for ", "")
                    if (bgp_session["bgp_state"] != 0 and bgp_session["bgp_time_in_state"] == 0 and line.find(
                            "Last reset") > 0):
                        line_split = line.split(",")
                        bgp_session["bgp_time_in_state"] = line_split[0].replace("Last reset", "").replace(" ", "")
                # print("something")
                bgp_session["bgp_address_family"] = address_family
                self.bgp_neighbors[bgp_session["bgp_neighbor_ip"]] = bgp_session
                # print(self.bgp_neighbors[address_family][bgp_session["neighbor_ip"]])
        self.ip_bgp_neighbor = self.bgp_neighbors

        return self.bgp_neighbors

    def set_mpls_ldp_interfaces(self, address_family="ipv4 unicast"):
        if not hasattr(self, "ospf_interfaces"):
            # self.set_ip_ospf_interface()
            pass
        connection = self.connect()
        command = "show mpls interfaces"
        show_mpls_interface = self.send_command(connection, command, self.hostname, timeout=5).replace("\t", "")
        # neighbor_string_split = show_bgp_neighbors.split("BGP neighbor is ")
        command = "show mpls ldp neighbor detail"
        show_mpls_ldp_neighbor = self.send_command(connection, command, self.hostname, timeout=5).replace("\t", "")
        show_mpls_interface = re.sub(' +', " ", show_mpls_interface)
        mpls_interface_lines = show_mpls_interface.split("\n")

        interfaces_mpls = {}
        for mpls_interface_line in mpls_interface_lines[3:]:
            mpls_interface_line_split = mpls_interface_line.split(" ")
            interface = mpls_interface_line_split[0].replace("TenGigE", "Te").replace("HundredGigE", "Hu").replace(
                "GigabitEthernet", "Gi").replace(" ", "")
            configured = mpls_interface_line_split[1]
            operational = mpls_interface_line_split[3].find("Yes") > -1
            ldp = configured.find("Yes") > -1
            ip_configured = configured.find("Yes") > -1
            interfaces_mpls[interface] = {"interface": interface, "ldp_enable": ldp,
                                          "ldp_operational_mpls": operational, "ldp_ip_configured": ip_configured}
            interfaces_mpls[interface]["ldp_neighbor_ip"] = "0.0.0.0"
            interfaces_mpls[interface]["ldp_state"] = False

        ldp_neighbor = {}

        strings_per_ldp_neighbor = show_mpls_ldp_neighbor.split("Peer LDP Identifier: ")

        strings_per_ldp_neighbor.pop(0)
        for string_ldp_neighbor in strings_per_ldp_neighbor:
            password = string_ldp_neighbor.find("MD5") > -1
            lines_ldp_neighbor = string_ldp_neighbor.split("\n")
            interfaces = {}
            neighbor_ip = lines_ldp_neighbor.pop(0).replace(":0", "").replace(" ", "")
            state = string_ldp_neighbor.find("State: Oper;") > -1
            for line_ldp_neighbor in lines_ldp_neighbor:

                if line_ldp_neighbor.find("Up time:") > -1:
                    uptime = line_ldp_neighbor.split(";")[0].replace("  Up time:", "").replace(" ", "")
            interfaces_neighbor_split = \
            string_ldp_neighbor.split("LDP Discovery Sources:")[1].split("Addresses bound to this peer:")[0].split("\n")

            for interface_neighbor in interfaces_neighbor_split:
                if (interface_neighbor.find("Targeted Hello") == -1):
                    interface = interface_neighbor.replace(" ", "").replace("\t", "").replace("TenGigE", "Te").replace(
                        "HundredGigE", "Hu").replace("GigabitEthernet", "Gi").replace(" ", "")
                    if interface != "":
                        interfaces[interface] = {"interface": interface, "ldp_ip": "0.0.0.0"}

                        interfaces_mpls[interface]["ldp_neighbor_ip"] = neighbor_ip
                        interfaces_mpls[interface]["ldp_state"] = state
                        interfaces_mpls[interface]["interface"] = interface

            ldp_neighbor[neighbor_ip] = {"ip": neighbor_ip, "state": state, "password": password,
                                         "interfaces": interfaces, "uptime": uptime}
        self.ldp_neighbors = ldp_neighbor
        self.mpls_ldp_interfaces = interfaces_mpls

        return ldp_neighbor, interfaces_mpls

    def set_pim_interfaces(self):

        connection = self.connect()
        command1 = 'show running-config formal router pim address-family ipv4 | i enable'
        show_run_pim = self.send_command(connection, command1, self.hostname, timeout=5)
        show_run_pim = show_run_pim.replace("router pim address-family ipv4 interface ", "").replace(" enable", "")
        command2 = 'show pim neighbor  | e "\\\*" | b Nei'
        show_pim_neighbor = self.send_command(connection, command2, self.hostname, timeout=5)
        command3 = 'show pim interface  | i on'
        show_pim_interface = self.send_command(connection, command3, self.hostname, timeout=5)

        interfaces = {}
        for pim_enable_interface in show_run_pim.split("\n")[1:]:
            pim_enable_interface = pim_enable_interface.replace("TenGigE", "Te").replace("HundredGigE", "Hu").replace(
                "GigabitEthernet", "Gi")
            interfaces[pim_enable_interface] = {"interface": pim_enable_interface,
                                                "pim_state": False, "pim_neighbor": "0.0.0.0",
                                                "pim_neighbor_count": "0",
                                                "pim_hello_timer": "0",
                                                "pim_dr_priority": 0,
                                                "pim_dr": "0.0.0.0"}

        # se eliminan los espacios extras para normalizar la tabla
        show_pim_neighbor = re.sub(' +', " ", show_pim_neighbor)
        show_pim_interface = re.sub(' +', " ", show_pim_interface)

        for pim_enable_interface in show_pim_interface.split("\n")[1:]:
            pim_enable_interface = pim_enable_interface.split(" ")
            ip_interface = pim_enable_interface[0]
            interface = pim_enable_interface[1].replace("TenGigE", "Te").replace("HundredGigE", "Hu").replace(
                "GigabitEthernet", "Gi")
            neighbor_count = pim_enable_interface[3]
            hello_timer = pim_enable_interface[4]
            dr_priority = pim_enable_interface[5]
            dr = pim_enable_interface[5] if pim_enable_interface[6].find("this") == -1 else ip_interface

            if (hasattr(interfaces, interface)):
                interfaces[interface]["pim_neighbor_count"] = neighbor_count
                interfaces[interface]["pim_hello_timer"] = hello_timer
                interfaces[interface]["pim_dr_priority"] = dr_priority
                interfaces[interface]["pim_dr"] = dr

        pim_neighbors = {}
        for pim_neighbor in show_pim_neighbor.split("\n")[3:]:
            pim_neighbor = pim_neighbor.split(" ")
            ip_neighbor = pim_neighbor[0]
            interface = pim_neighbor[1].replace("TenGigE", "Te").replace("HundredGigE", "Hu").replace("GigabitEthernet",
                                                                                                      "Gi")
            uptime = pim_neighbor[2]

            pim_neighbors[ip_neighbor] = {"ip_neighbor": ip_neighbor, "interface": interface, "uptime": uptime}
            if hasattr(interfaces, interface) != False:
                interfaces[interface]["pim_state"] = True if ip_neighbor != "0.0.0.0" else False
                interfaces[interface]["pim_neighbor"] = ip_neighbor

        # print("finish XR")
        self.pim_interfaces = interfaces
        self.pim_neighbors = pim_neighbors

        return interfaces, pim_neighbors

    def set_interface(self, index):
        interface = InterfaceXR(self, index)
        # print("adentro del metodo", index)
        self.interfaces[index] = interface

    def get_ip_ospf_processes(self):
        '''

        :return:

            This methid will return an array of the configured ospf proceses and vrf in
            the device
            [{process_id:String,
            vrf:string}]
            if the proceess is in global routing table it will return
            process id and vrf : "global"

        '''

        command_vrf = "show ospf vrf all "
        command_gobal = "show ospf "

        process_list = []
        process_vrf_list = []
        connection = self.connect()
        output_vrf = self.send_command(connection=connection, command=command_vrf)
        output_global = self.send_command(connection=connection, command=command_gobal)
        self.close(connection)
        split_process_vrf = output_vrf.split("VRF ")
        split_process_vrf.pop(0)
        for process in split_process_vrf:
            process_line = process.split("\n")[0]

            vrf = process_line.split(" ")[0]
            ospf_id = process_line.split("ID ")[1]
            process_id = process_line.split("\"ospf ")[1].split("\"")[0]
            process_vrf_list.append(process_id)
            process_list.append({"ospf_process_id": process_id, "vrf": vrf, "ospf_id": ospf_id})
        split_process = output_global.split("Routing Process")
        split_process.pop(0)
        for process in split_process:
            process_line = process.split("\n")[0]
            process_id = process_line.split("ospf ")[1].split("\"")[0]
            ospf_id = process_line.split("ID ")[1]
            if (process_id not in process_vrf_list):
                process_list.append({"ospf_process_id": process_id, "vrf": "global", "ospf_id": ospf_id})

        self.self_ospf_process_list = process_list

        return self.self_ospf_process_list

    def create_policies_bgp_neighbors(self, address_family="ipv4 unicast", country_key="CR", conection_type="CUS"):
        if (hasattr(self, "bgp_neighbors")):
            if not address_family in self.bgp_neighbors:
                self.set_ip_bgp_neighbors(address_family)
        else:
            self.set_ip_bgp_neighbors(address_family)
        connection = self.connect()
        result = ""
        for ip, neighbor in self.bgp_neighbors.items():
            if (neighbor["bgp_description"].find(conection_type) > -1):
                result += "---------------------------------------\n"
                result += "data \n"
                result += "as || " + neighbor["bgp_remote_as"] + " || ip " + ip + "  description " + neighbor[
                    "bgp_description"] + "\n"
                result += "---------------------------------------\n"
                result += "policies\n"
                result += "router bgp 52468 vrf INTERNET nei " + ip + " address-family ipv4 unicast route-policy " + "RPL" + country_key + "IN" + "IP4" + conection_type + \
                          neighbor["bgp_description"] + " in " + "\n"
                result += "router bgp 52468 vrf INTERNET nei " + ip + " address-family ipv4 unicast route-policy " + "RPL" + country_key + "OT" + "IP4" + conection_type + \
                          neighbor["bgp_description"] + " out " + "\n"
                result += " route-policy " + "RPL" + country_key + "IN" + "IP4" + conection_type + neighbor[
                    "bgp_description"] + "\n"
                result += " if destination in  " + "PFX" + country_key + "IN" + "IP4" + conection_type + neighbor[
                    "bgp_description"] + " then \n"
                result += "set community (52468:10XXX," + neighbor["bgp_remote_as"][
                                                          -5:] + ":52468,52468:1XXX,52468:20410,52468:20510,52468:20610,52468:20530" + \
                          ",52468:20120,52468:20220,52468:20420,52468:20520,52468:20729,52468:20620) \n"
                result += "endif \n"
                result += "end\n"
                result += " prefx-set " + "PFX" + country_key + "IN" + "IP4" + conection_type + neighbor[
                    "bgp_description"] + "\n"
                result += " route-policy " + "RPL" + country_key + "OT" + "IP4" + conection_type + neighbor[
                    "bgp_description"] + "\n"

                result += " shows --------\n"

                result += "show run route-policy " + neighbor["bgp_policy_out"] + "\n"
                result += self.send_command(connection, "show run route-policy " + neighbor["bgp_policy_out"])
                result += "show run route-policy " + neighbor["bgp_policy_in"] + "\n"
                result += self.send_command(connection, "show run route-policy " + neighbor["bgp_policy_in"])

                result += self.send_command(connection,
                                            "show run prefix-set " + neighbor["bgp_policy_in"].replace("-IN", ""))
                result += "---------------------------------------\n"

        print(result)

    def get_bgp_neighbor_advertised_routes(self, bgp_neigbor_ip, address_family="ipv4 unicast", save_networks=False):

        command = "show bgp " + address_family + " neigh " + bgp_neigbor_ip + " advertised-routes "
        connection = self.connect()
        output = self.send_command(command=command, connection=connection)

        lines = output.split("\n")
        bgp_advertised_prefixes = {}
        if (address_family.find("ipv6") > -1):
            has_next_prefix = True
            index = 3
            while has_next_prefix:
                jump = 3
                if ((len(lines) >= index + jump - 1)):

                    if (lines[index + jump].find("/") > -1):
                        print("NEXT JUMP " + lines[index + jump])
                        as_path = re.sub(" +", " ", lines[index + 2])
                        if (as_path.find("Local") == -1):
                            prefix = re.sub(" +", " ", lines[index])

                            network = prefix.split(" ")[0]
                            next_hop = prefix.split(" ")[1]
                            bgp_from = re.sub(" +", "", lines[index + 1])

                        else:
                            network = re.sub(" +", "", lines[index])
                            next_hop = re.sub(" +", "", lines[index + 1])
                            bgp_from = "Local"
                            as_path = as_path.replace("Local", "")

                    else:
                        jump = 4
                        network = re.sub(" +", "", lines[index])
                        next_hop = re.sub(" +", "", lines[index + 1])
                        bgp_from = re.sub(" +", "", lines[index + 2])
                        as_path = re.sub(" +", " ", lines[index + 3])
                    index = index + jump
                    prepends = as_path.count("52468")
                    bgp_advertised_prefixes[network] = {"network": network, "next_hop": next_hop, "bgp_from": bgp_from,
                                                        "as_path": as_path}
                else:
                    has_next_prefix = False
        else:
            for line in lines[3:]:
                if (len(line) > 51):
                    network = line[0:18].replace(" ", "")
                    next_hop = line[19:34].replace(" ", "")
                    bgp_from = line[34:50]
                    as_path = line[51:]
                    prepends = as_path.count("52468")
                bgp_advertised_prefixes[network] = {"network": network, "next_hop": next_hop, "bgp_from": bgp_from,
                                                    "as_path": as_path, "prepends": str(prepends)}

        if (save_networks):
            if hasattr(self, "ip_bgp_neighbors"):
                self.set_ip_bgp_neighbors(address_family=address_family)
            self.bgp_neighbors[bgp_neigbor_ip]["advertised_routes"] = bgp_advertised_prefixes
        return bgp_advertised_prefixes

    def print_bgp_advertise(self, bgp_neigbor_ip, address_family="ipv4 unicast"):
        result = self.get_bgp_neighbor_advertised_routes(bgp_neigbor_ip, address_family)
        output = ""
        columns = ""
        for prefix, prefix_info in result.items():
            if (columns == ""):
                columns += "IPT!"
                for column, data in prefix_info.items():
                    columns += column + "!"
                output += columns + "\n"
            output += bgp_neigbor_ip + "!"
            for column, data in prefix_info.items():
                output += data + "!"
            output += "\n"
        return output

    def set_ip_ipt_bgp_neighbors(self, address_family="ipv4 unicast"):

        if not hasattr(self, "ip_bgp_neighbors"):
            self.set_ip_bgp_neighbors(address_family=address_family)
        self.ip_ipt_bgp_neighbors = {}
        for ip_bgp_neighbor, neighbor in self.bgp_neighbors.items():
            if (neighbor["bgp_address_family"] == address_family and neighbor["bgp_description"].find("IPT") > -1):
                self.ip_ipt_bgp_neighbors[ip_bgp_neighbor] = neighbor

    def set_ipt_bgp_advertised_routes(self, address_family="ipv4 unicast"):

        if not hasattr(self, "ip_ipt_bgp_neighbors"):
            self.set_ip_ipt_bgp_neighbors(address_family=address_family)

        for ip_bgp_neighbor, neighbor in self.ip_ipt_bgp_neighbors.items():
            self.get_bgp_neighbor_advertised_routes(bgp_neigbor_ip=ip_bgp_neighbor, address_family=address_family,
                                                    save_networks=True)

    def search_ipt_advertised_prefix(self, prefix_list, address_family="ipv4 unicast", result=[]):
        if (not hasattr(self, "ip_ipt_bgp_neighbors")):
            self.set_ipt_bgp_advertised_routes(address_family=address_family)

        for ip_neighbor, neighbor in self.ip_ipt_bgp_neighbors.items():
            # print(neighbor["advertised_routes"])
            for prefix in prefix_list:
                # print(prefix)
                if (prefix in neighbor["advertised_routes"]):

                    prefix_data = {"ipp": self.display_name, "ASN EBGP": neighbor["bgp_remote_as"],
                                   "neighbor": ip_neighbor, "description": neighbor["bgp_description"]}

                    for key, item in neighbor["advertised_routes"][prefix].items():
                        prefix_data[key] = item

                    result.append(prefix_data)
        # pprint(list)
        return result

    def get_bgp_neighbor_received_routes(self, bgp_neigbor_ip, address_family="ipv4 unicast", save_networks=False):

        command = "show bgp " + address_family + " neigh " + bgp_neigbor_ip + " received routes "
        connection = self.connect()
        output = self.send_command(command=command, connection=connection)

        lines = output.split("*  ")
        lines.pop(0)
        bgp_recived_routes = {}
        for line in lines:

            if (address_family.find("ipv6") > -1):
                # ipv6 trataimento especial
                line = line.split("Processed")[0]
                prefix = line.split("\n")[0]
                prefix = re.sub(" +", " ", prefix)

                med_as = line.split("\n")[1][61:]
                network = prefix.split(" ")[0]
                next_hop = prefix.split(" ")[1]
                med = med_as.split(" ")[0]
                as_path = med_as.replace(med, "")
            else:
                # ipv4
                line = line.replace("\n", "").split("Processed")[0]

                network = line[0:18].replace(" ", "")
                next_hop = line[18:41].replace(" ", "")
                med_as = line[58:]
                med = med_as.split(" ")[0]
                as_path = med_as.replace(med, "")
            bgp_recived_routes[network] = {"network": network, "next_hop": next_hop, "med": med, "as_path": as_path}
        if (save_networks):
            if not hasattr(self, "ip_bgp_neighbors"):
                self.set_ip_bgp_neighbors()
            self.ip_bgp_neighbors[bgp_neigbor_ip]["recived_routes"] = bgp_recived_routes
        return (bgp_recived_routes)

    def set_interfaces(self, template_name="show_interfaces_detail_ios.template"):
        pprint(self)
        super().set_interfaces(template_name=template_name)

    def configure_snmp_location(self, text):
        command = "configure terminal \n snmp-server location " + text + "\ncommit\nexit\n"
        print(self.ip, command)
        print(self.send_command(command=command, connection=self.connect()))

    """
    def get_kivy_policy_rate(self):
        summary_policy = self.get_summarize_rate()
        keys ={}
        keys["in"]= ["bw",
                 "ENTRADAINTERNETTELGUA",
                 "ENTRADAINTERNETSALVADOR",
                 "ENTRADAINTERNET_COSTARICA",
                 "ENTRADAINTERNETNICARAGUA",
                 "ENTRADAINTERNETHONDURAS",
                 "class-default",
                 "total",
                 "%"
                 ]
        keys["out"]=["bw",
                 "SALIDAINTERNETTELGUA",
                 "SALIDAINTERNETSALVADOR",
                 "SALIDAINTERNETSERCOM",
                 "SALIDAINTERNETNICARAGUA",
                 "SALIDAINTERNETCOSTARICA",
                 "class-default",
                 "total",
                 "%"
                ]
        connection = self.connect()
        ipp_policy_layout= BoxLayout(orientation="vertical",spacing=2)
        ipp_policy_layout.size_hint_x=1
        self.set_internet_interfaces()
        for index, interface in self.internet_interfaces.items():
            interface_layout = interface.get_kivy_policy_rate(connection=connection, parent_device=self, keys=keys)
            interface_layout.size_hint_x = 1
            ipp_policy_layout.add_widget(interface_layout)
        ipp_policy_layout.add_widget(self.get_kivy_summary_layout(keys=keys))
        return ipp_policy_layout

    def get_kivy_summary_layout(self, keys):

        summary_rate = self.get_summarize_rate()
        summary_layout = BoxLayout(orientation="horizontal", spacing=2)
        label_index = LabelB(text=self.display_name,
                             font_size=12,
                             bcolor=[0.5, 0.3, 0.2, 0.25],
                             size_hint=(0.05, 1))

        label_index.size_hint = (0.16, 1)
        label_tag = LabelB(text="total", font_size=12, bcolor=[0.6, 0.3, 0.2, 0.25])
        label_tag.size_hint = (0.14, 1)
        summary_layout.add_widget(label_index)
        summary_layout.add_widget(label_tag)
        for direction, key_set in keys.items():
            policy_direction_layout = BoxLayout(orientation="horizontal", spacing=2)
            if direction in summary_rate:

                for index in key_set:
                    if index in summary_rate[direction]:

                        values = summary_rate[direction][index]
                        colors = Interface.get_kivy_label_usage_color(index=index,
                                                                      value=values["transmited"],
                                                                      bw=summary_rate[direction]["bw"]["transmited"],
                                                                      total=summary_rate[direction]["total"]["transmited"],
                                                                      opacity=.7)

                        policy_direction_layout.add_widget(LabelB(text=str(round(values["transmited"], 2)),
                                                                  font_size=12,
                                                                  bcolor=colors["color"],
                                                                  color=colors["font_color"]))

            summary_layout.add_widget(policy_direction_layout)
        return summary_layout
        """
