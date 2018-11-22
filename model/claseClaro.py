import socket
from platform import system as system_name  # Returns the system/OS name
from subprocess import call   as system_call  # Execute a shell command
import datetime
import subprocess
from multiping import multi_ping
import threading as th
import pyyed
import shelve
import time
import os, sys
import socket
import random
from struct import pack, unpack
from datetime import datetime as dt

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto.rfc1902 import Integer, IpAddress, OctetString

import psycopg2 as pmsql
import xlwt

from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR

from pprint import pprint
import ipaddress


class Claro:

    def __init__(self):

        self.list_ipp = {}
        self.list_bgp_pe = {}
        self.list_pe_app = []
        self.ospf_as = "52468"
        self.bgp_as = "52468"
        self.dbname = "boip"
        self.dbuser = 'postgres'
        self.dbhost = 'localhost'
        self.dbpassword = 'epsilon123'
        self.max_threads = 50
        self.not_connected_devices = []

    def tabulate_mpls_traffic_tunnels(self, ip_lsr_router, filename="test_mpls"):
        lsr = CiscoIOS(master=self.master, ip=ip_lsr_router, display_name="lsr")
        lsr.set_mpls_te_tunnels()
        pprint(len(lsr.mpls_te_tunnels))
        mpls_te_data = lsr.mpls_te_tunnels
        cisco_sources = {}
        threads = []
        device_list = []
        result = []

        for tunnel_instance, tunnel in mpls_te_data.items():
            if (tunnel["source_ip"] not in cisco_sources):
                cisco_sources[tunnel["source_ip"]] = CiscoIOS(master=self.master, ip=tunnel["source_ip"],
                                                              display_name=tunnel["source_ip"])
        methods = {"set_pseudo_wire_class": "pseudo_wire_class",
                   "set_pseudowires": "pseudowire", "set_service_instances": 'service_instances',
                   "set_template_type_pseudowires": "template_type_pseudowires", "set_bridge_domains": "bridge_domains",
                   "set_vfis": "vfis"
                   }

        devices = self.dict_to_list(cisco_sources)
        self.excute_methods(methods=methods, devices=devices)

        for tunnel_instance, tunnel in mpls_te_data.items():
            if (tunnel["source_ip"] not in cisco_sources):
                cisco_sources[tunnel["source_ip"]] = CiscoIOS(master=self.master, ip=tunnel["source_ip"],
                                                              display_name=tunnel["source_ip"])
            device = cisco_sources[tunnel["source_ip"]]
            service_instance_data = device.get_service_instance_by_tunnel_id(tunnel_id=tunnel["tunnel_id"])
            if (service_instance_data != "null"):
                print(service_instance_data)
                tunnel["root_interface"] = service_instance_data["interface"]
                tunnel["root_service_instance"] = service_instance_data["service_instance"]
                tunnel["root_description"] = service_instance_data["description"]
                tunnel["root_dot1q"] = service_instance_data["dot1q"]
            else:
                service_instances_vfi = device.get_service_instance_by_tunnel_id_vfi(tunnel_id=tunnel["tunnel_id"])
                tunnel["root_interface"] = ""
                tunnel["root_service_instance"] = ""
                tunnel["root_description"] = ""
                tunnel["root_dot1q"] = ""
                pprint("interfaces VFI")
                print(service_instances_vfi)
                if service_instances_vfi:
                    for service_instance_data in service_instances_vfi:
                        tunnel["root_interface"] += service_instance_data["interface"] + " ! "
                        tunnel["root_service_instance"] += service_instance_data["service_instance"] + " ! "
                        tunnel["root_description"] += service_instance_data["description"] + " ! "
                        tunnel["root_dot1q"] += service_instance_data["dot1q"] + " ! "

        # pprint(mpls_te_data)

        self.save_to_excel_dict(mpls_te_data, filename)

    def dict_to_list(self, dict_input):
        data_list = []
        for index, data in dict_input.items():
            data_list.append(data)
        return data_list

    def save_to_excel_dict(self, dictionay_data, file_name):
        data_list = self.dict_to_list(dict_input=dictionay_data)
        self.save_to_excel_list(data_list, file_name)

    def save_to_excel_list(self, list_data, file_name):


        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet("data")

        rows_skipped = 1

        columns = list_data[0].keys()
        for colidx, column in enumerate(columns):
            worksheet.write(rows_skipped, colidx, column)

        for rowidx, row in enumerate(list_data):

            for colindex, col in enumerate(columns):

                if (col in row):
                    try:
                        data = row[col]
                        worksheet.write(rowidx + rows_skipped + 1, colindex, data)
                    except:
                        data = row[col]
                        print(colindex)
                        print(col)
                        print(data)

        workbook.save(file_name + '.xls')

    def create_ospf_area_graph(self, output_database):

        '''\
        split by Link
          LS age:
          split by  Link connected to:
            index [0]
            split by "\n
                index[3].split "  Link State ID: " [1]
                add collection id [node]=[]
            index [0-3]
            split by "\n"
                
        '''
        routers = {}
        link_states_entries = output_database.split("LS age:")[1:]
        for router_lsa in link_states_entries:
            ls_break_down = router_lsa.split("Link connected to:")
            router_information = ls_break_down[0].split("\n")[3].split("Link State ID: ")[1]
            print(router_information)
            ip = router_information
            routers[router_information] = {}
            community = 'snmpUfi'
            routers[router_information]["hostname"] = self.poll_snmp_hostname(ip, community)
            if routers[router_information]["hostname"] == "no_snmp":
                community = 'pnrw-med'
                routers[router_information]["hostname"] = self.poll_snmp_hostname(ip, community)
            router_interfaces = ls_break_down[1:]
            routers[router_information]["plattform"] = self.poll_snmp_plattform(ip, community)
            interfaces = []
            for interface in router_interfaces:
                interace_split = interface.split("\n")
                interface_data = {}
                interface_type = interace_split[0].replace(" a ", "").replace(" a", "a")
                interface_data["interface_type"] = interface_type
                if (interface_type == "Stub Network"):
                    interface_data["interface_network"] = interace_split[1].split(": ")[1]
                    interface_data["interface_mask"] = interace_split[2].split(": ")[1]
                else:
                    interface_data["neighbor_ip"] = interace_split[1].split(": ")[1]
                    interface_data["interface_ip"] = interace_split[2].split(": ")[1]
                    address = ipaddress.IPv4Interface(interface_data["interface_ip"] + "/30")
                    interface_data["interface_network"] = str(address.network)
                    interface_name = self.poll_snmp_interface_name_ip(router_information, community,
                                                                      interface_data["interface_ip"])
                    interface_name = CiscoIOS.get_normalize_interface_name(interface_name)
                    interface_data["interface_name"] = interface_name
                interface_data["cost"] = interace_split[4].split(": ")[1]
                interfaces.append(interface_data)
            routers[router_information]["interfaces"] = interfaces
        stubs = {}
        point_to_point = {}
        pprint(routers)
        for router, data in routers.items():
            for interface in data["interfaces"]:

                if interface["interface_type"] != "Stub Network":
                    if not interface["interface_network"] in point_to_point:
                        point_to_point[interface["interface_network"]] = [{"local_router": router,
                                                                           "interface_ip": interface["interface_ip"],
                                                                           "neighbor_ip": interface["neighbor_ip"],
                                                                           "interface_name": interface[
                                                                               "interface_name"],
                                                                           "cost": interface["cost"]}]
                    else:
                        point_to_point[interface["interface_network"]].append({"local_router": router,
                                                                               "interface_ip": interface[
                                                                                   "interface_ip"],
                                                                               "neighbor_ip": interface["neighbor_ip"],
                                                                               "interface_name": interface[
                                                                                   "interface_name"],
                                                                               "cost": interface["cost"]})
                else:
                    if not interface["interface_network"] + "/30" in point_to_point:
                        if not interface["interface_network"] in stubs:
                            stubs[interface["interface_network"]] = [{"local_router": router}]
                        else:
                            stubs[interface["interface_network"]].append({"local_router": router})

        return routers, point_to_point, stubs

    def poll_snmp_plattform(self, ip, community):

        platfforms = {"9K": "ASR9K", "ASR920": "ASR920", "900": "ASR900", "default": 'null'}
        cmdGen = cmdgen.CommandGenerator()
        oid = "	1.3.6.1.2.1.1.1"
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.nextCmd(cmdgen.CommunityData(community),
                                                                            cmdgen.UdpTransportTarget(
                                                                                (ip, 161)),
                                                                            oid
                                                                            )
        plattform = platfforms["default"]
        snmp_value = "null"
        for val in varBinds:
            snmp_value = str(val[0][1]).split("\n")[0]

        for pattern, plattform_name in platfforms.items():
            if (snmp_value.find(pattern) > -1):
                return plattform_name
        return plattform

    def poll_snmp_hostname(self, ip, community):
        value = "1.3.6.1.2.1.1.5.0"
        cmdGen = cmdgen.CommandGenerator()
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(cmdgen.CommunityData(community),
                                                                           cmdgen.UdpTransportTarget(
                                                                               (ip, 161)),
                                                                           value
                                                                           )
        hostname = "no_snmp"
        for name, val in varBinds:
            hostname = str(val).split(".")[0]
        return hostname

    def poll_snmp_interface_index_ip(self, ip, community, ip_interface):
        cmdGen = cmdgen.CommandGenerator()
        oid = "1.3.6.1.2.1.4.20.1.2." + ip_interface
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(cmdgen.CommunityData(community),
                                                                           cmdgen.UdpTransportTarget(
                                                                               (ip, 161)),
                                                                           oid

                                                                           )
        snmp_interface_index = "null"
        for val in varBinds:
            snmp_interface_index = str(val[1])
        return snmp_interface_index

    def poll_snmp_interface_name_index(self, ip, community, index):
        cmdGen = cmdgen.CommandGenerator()
        oid = "1.3.6.1.2.1.2.2.1.2." + index
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(cmdgen.CommunityData(community),
                                                                           cmdgen.UdpTransportTarget(
                                                                               (ip, 161)),
                                                                           oid
                                                                           )
        interface_name = "null"
        for val in varBinds:
            interface_name = str(val[1])
        return interface_name

    def poll_snmp_interface_name_ip(self, ip, community, ip_interface):
        index = self.poll_snmp_interface_index_ip(ip, community, ip_interface)
        if index != "null":
            interface_name = self.poll_snmp_interface_name_index(ip, community, index)
            return interface_name
        else:
            return "null"

    def generate_yed_ospf_area(self, output_database, file_name="prueba3"):
        grid_width = 10
        grid_x_counter = 0
        grid_y_counter = 0
        separation = 150
        routers, point_to_point, stubs = self.create_ospf_area_graph(output_database)
        g = pyyed.Graph()
        node_colors = {"-CER": "#33ccff", "-AGG": "#66ff99", "-C": "#ff9966", "-ACC": "#cc99ff", "default": "#999966"}
        interface_colors = {"Te": "#0099cc", "Gi": "#ff5050", "default": "#00cc99"}
        plattform_shapes = {"ASR9K": "rectangle3d", "ASR920": "hexagon", "ASR900": "octagon", 'null': "diamond"}
        '''
        "rectangle", "rectangle3d", "roundrectangle", "diamond", "ellipse",
        "fatarrow", "fatarrow2", "hexagon", "octagon", "parallelogram",
        "parallelogram2", "star5", "star6", "star6", "star8", "trapezoid",
        "trapezoid2", "triangle", "trapezoid2", "triangle"
        '''
        for router, data in routers.items():
            bcolor = node_colors["default"]
            shape = plattform_shapes[data["plattform"]]
            for name, color in node_colors.items():
                if (data["hostname"].find(name) > -1):
                    bcolor = color

            g.add_node(node_name=router, height=str(200), width=str(200), shape=shape,
                       x=str(grid_x_counter * separation), y=str(grid_y_counter * separation), shape_fill=bcolor)
            label_text = data["hostname"]
            g.nodes[router].add_label(label_text)
            if grid_x_counter == 9:
                grid_x_counter = 0
                grid_y_counter = grid_y_counter + 1
            else:
                grid_x_counter = grid_x_counter + 1

        for id, edge in point_to_point.items():
            if len(edge) > 1:
                label = edge[0]["interface_name"] + " C:" + edge[0]["cost"]
                label2 = edge[1]["interface_name"] + " C:" + edge[1]["cost"]
                lcolor = interface_colors["default"]
                for interface, color in interface_colors.items():
                    if label.find(interface) > -1:
                        lcolor = color

                g.add_edge(edge[0]["local_router"], edge[1]["local_router"], id=str(id), label=label, label2=label2,
                           color=lcolor, width="2.0")

        file = open(file_name + ".graphml", "w")
        file.write(g.get_graph())

    def search_recived_routers_ipt_advertise(self, ip_pe, display_name_pe, bgp_neigbor_description_filter,
                                             address_family="ipv4 unicast", print_on_screen=True, sep="|"):

        device = CiscoXR(display_name=display_name_pe, ip=ip_pe, platform="XR", master=self.master)
        device.set_ip_bgp_neighbors(address_family=address_family)
        for bgp_neigbor_ip, neighbor in device.bgp_neighbors.items():
            if (neighbor["bgp_description"].find(bgp_neigbor_description_filter) > -1):
                prefixes = self.get_recived_prefix_pe_bgp_neighbor(device, display_name_pe, bgp_neigbor_ip,
                                                                   address_family)
                real_prefixes = prefixes.keys()
                print("============================================================\n\n")
                print(neighbor["bgp_description"] + "    " + bgp_neigbor_ip + "\n\n")
                self.search_ipt_prefix_advertisement(prefix_list=real_prefixes, address_family=address_family)

    def get_recived_prefix_pe_bgp_neighbor(self, bgp_device, display_name_pe, bgp_neigbor_ip,
                                           address_family="ipv4 unicast", print_on_screen=True, sep="|"):

        prefixes = bgp_device.get_bgp_neighbor_received_routes(bgp_neigbor_ip=bgp_neigbor_ip,
                                                               address_family=address_family)

        # pprint(prefixes)
        return prefixes

    def search_ipt_prefix_advertisement(self, prefix_list, address_family="ipv4 unicast", print_on_screen=True,
                                        sep="|"):
        if (len(self.list_ipp) == 0):
            self.init_ipp()
        threads = []
        device_list = []
        result = []
        for ip, device in self.list_ipp.items():
            t = th.Thread(target=device.search_ipt_advertised_prefix,
                          kwargs={"prefix_list": prefix_list, "address_family": address_family, "result": result})
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        if (print_on_screen):
            output = ""
            if (len(result) > 0):
                for key, data in result[0].items():
                    output += key + sep
                output += "\n"
                for item in result:
                    for key, data in item.items():
                        output += data + sep
                    output += "\n"
                print(output)
            else:
                print("no se ven los prefijos publicados en ufinet")

    def init_ipp(self):

        self.list_ipp["10.235.252.15"] = CiscoXR("10.235.252.15", "NAP_1", self.master)
        self.list_ipp["10.235.252.18"] = CiscoXR("10.235.252.18", "NAP_2", self.master)

    # master es el objeto que se utiliza para configuracion inicial contiene las contrasenas del acs
    # del usuario en cuestion

    def init_bgp_pe(self):
        self.list_bgp_pe["10.235.252.15"] = CiscoXR("10.235.252.15", "NAP_1_9K", self.master)
        self.list_bgp_pe["10.235.252.18"] = CiscoXR("10.235.252.18", "NAP_2_9K", self.master)
        self.list_bgp_pe["10.250.55.225"] = CiscoXR("10.250.55.225", "GT_GUY_9K", self.master)
        self.list_bgp_pe["10.234.5.194"] = CiscoXR("10.234.5.194", "CR_SPE_9K", self.master)
        self.list_bgp_pe["10.234.5.171"] = CiscoXR("10.234.5.171", "CR_ESC_9k", self.master)
        self.list_bgp_pe["10.244.1.12"] = CiscoIOS("10.244.1.12", "HN_TEG_1000", self.master)
        self.list_bgp_pe["10.243.1.8"] = CiscoIOS("10.243.1.8", "SV_SMA_1000", self.master)
        self.list_bgp_pe["192.168.205.55"] = CiscoIOS("192.168.205.55", "PN_PTY_1000", self.master)
        self.list_bgp_pe["192.168.205.55"].set_jump_gateway("10.250.55.3", "telnet")
        self.list_bgp_pe["192.168.250.33"] = CiscoIOS("192.168.250.33", "NI_PTY_1000", self.master)
        self.list_bgp_pe["192.168.250.33"].set_jump_gateway("10.250.55.3", "telnet")

    def recollect_ospf_topology(self, initial_device_rid="172.16.30.3", shelve_name="prueba"):
        thread_count = 10
        topology = shelve.open(shelve_name)
        dict_ospf_neigbors = {}
        initial_devices = [CiscoIOS(ip=initial_device_rid, display_name="initial_device", master=self.master)]
        global_not_conected = []
        working_devices = self.correct_device_platform(initial_devices)
        new_working_devices = []

        while len(working_devices) > 0:
            threads = []
            while len(threads) < thread_count and len(working_devices) > 0:
                device = working_devices.pop()
                if (device.ip not in dict_ospf_neigbors):
                    t = th.Thread(target=device.set_ospf_topology,
                                  kwargs={"new_working_devices": new_working_devices,
                                          "dict_ospf_neigbors": dict_ospf_neigbors})
                    t.start()
                    threads.append(t)
            for t in threads:
                t.join()

            new_working_devices, not_connected = self.clean_list_devices(new_working_devices)
            working_devices = self.correct_device_platform(new_working_devices)
            global_not_conected.append(not_connected)

    def graph_bgp_adjacencies(self, graph, device, line_types="line", address_family="ipv4 unicast", vrf="default",
                              filter_description="", shape="rectangle", color="#000000", size="100",
                              shape_fill="#121212"):
        connection = device.connect()
        counter = 0
        for ip, bgp_neighbor in device.bgp_neighbors.items():
            if (bgp_neighbor["bgp_state"] == 'Established'):
                if (bgp_neighbor["bgp_description"].find(filter_description) > -1):
                    counter += 1
                    id = str(counter) + filter_description + device.display_name
                    graph.add_node(node_name=bgp_neighbor["bgp_description"] + " " + ip, font_size="24",
                                   shape_fill=color, height=size, width=size,
                                   shape=shape)
                    network, interface = device.get_interface_route(connection=connection, vrf=vrf, address=ip)
                    graph.add_edge(node1=device.display_name, node2=bgp_neighbor["bgp_description"] + " " + ip, id=id,
                                   label="", label2="", width="2.0",
                                   color=color, arrowfoot="none", line_type=line_types)
                    pprint(device.display_name)
                    pprint(device.interfaces.keys())
                    device.set_interfaces_stats(interfaces_index=[interface])
                    rate = str(device.interfaces[interface].rate_out)
                    graph.edges[id].add_aditional_label(text=str(interface), color="#000000", position="scenter",
                                                        size="20")
                    graph.edges[id].add_aditional_label(text=str(rate), color="#000555", position="shead",
                                                        size="20")

                    '''
                    graph.edges[id].add_aditional_label(text="BGP OT " + str(bgp_neighbor["bgp_total_prefixes_advertised"]),
                                                         color="#933b00",
                                                         position="stail", size="12")
                    graph.edges[id].add_aditional_label(text="BGP IN " + str(bgp_neighbor["bgp_accepted_prefixes"]),
                                                         color="#0442a5",position="shead", size="12")
                                                         '''
                    graph.edges[id].add_aditional_label(text="AS" + str(bgp_neighbor["bgp_remote_as"]),
                                                        color="#000000", position="tcenter", size="12")

    def internet_test(self, test_name):
        self.init_bgp_pe()
        devices = self.list_bgp_pe
        threads = []
        for ip, device in devices.items():
            vrf = "INTERNET" if isinstance(device, CiscoXR) else "default"
            device.internet_validation_arp(test_name=test_name, vrf=vrf)
            time.sleep(10)

        devices_data = {}

        for ip, device in devices.items():
            device_shelve = shelve.open(test_name + device.display_name)
            device_data = {}
            device_data["responses"] = device_shelve["responses"]
            device_data["no_responses"] = device_shelve["no_responses"]
            if "test_no_responses" in device_shelve:
                device_data["test_no_responses"] = device_shelve["test_no_responses"]
            devices_data[device.display_name] = device_data

        return devices_data

    def set_bgp_neighbors(self, address_family="ipv4 unicast", vrf="default"):
        th.Thread()
        ready_devices = []
        devices = self.list_bgp_pe
        threads = []
        for ip, device in devices.items():
            add_name = "vrf " + vrf + " " + address_family if isinstance(device, CiscoXR) else address_family

            t = th.Thread(target=device.set_ip_bgp_neighbors, kwargs={"address_family": add_name})
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        threads = []
        edges = {}
        g = pyyed.Graph()
        for ip, device in devices.items():
            vrf = vrf if isinstance(device, CiscoXR) else "default"
            color = "#42cbf4"
            shape = "roundrectangle"
            if (device.display_name.find("NAP") > -1):
                color = "#877ac9"
                shape = "octagon"
            address_list = []
            g.add_node(node_name=device.display_name, font_size="24", shape_fill=color, height="175.0", width="175.0",
                       shape=shape)

            self.graph_bgp_adjacencies(graph=g, device=device, line_types="dashed",
                                       address_family=address_family, vrf=vrf, filter_description="CDN",
                                       shape="roundrectangle", color="#425ff4", shape_fill="#7d829b")
            self.graph_bgp_adjacencies(graph=g, device=device, line_types="dashed",
                                       address_family=address_family, vrf=vrf, filter_description="PNI",
                                       shape="trapezoid2", color="#177a63", shape_fill="#28ad1d")
            self.graph_bgp_adjacencies(graph=g, device=device, line_types="dashed",
                                       address_family=address_family, vrf=vrf, filter_description="IPT",
                                       shape="ellipse", color="#b28d35", shape_fill="#b78612")

            for ip_neighbor, bgp_neighbor in device.bgp_neighbors.items():
                if (bgp_neighbor["bgp_state"] == 'Established'):
                    if (bgp_neighbor["bgp_remote_as"] == "52468"):
                        address_list.append(ip_neighbor)

            t = th.Thread(target=device.get_interfaces_address, kwargs={"vrf": vrf, "list_address": address_list})
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        for ip, device in devices.items():

            for ip_neighbor, bgp_neighbor in device.bgp_neighbors.items():
                if (bgp_neighbor["bgp_remote_as"] == "52468" and bgp_neighbor["bgp_state"] == 'Established'):
                    network = device.prefix_per_interface[ip_neighbor]["network"]
                    interface = device.prefix_per_interface[ip_neighbor]["interface"]
                    data = {"device": device, "ip_neighbor": ip_neighbor,
                            "bgp_description": bgp_neighbor["bgp_description"],
                            "interface": interface, "node": device.display_name,
                            "bgp_total_prefixes_advertised": bgp_neighbor["bgp_total_prefixes_advertised"],
                            "bgp_accepted_prefixes": bgp_neighbor["bgp_accepted_prefixes"]}
                    if network in edges:
                        edges[network].append(data)
                    else:
                        edges[network] = [data]
        id = 0
        for network, edge in edges.items():
            id += 1
            if (len(edge) == 2):
                if (edge[0]["node"].find("NAP") > -1 or edge[1]["node"].find("NAP") > - 1):
                    color = "#db8823"
                else:
                    if (edge[0]["node"].find("ESC") > -1 or edge[1]["node"].find("GUY") > - 1):
                        color = "#a7f213"
                    else:
                        color = "#87bfb8"

                label = (edge[0]["interface"].replace("nGigE", "")) + " " + edge[1]["ip_neighbor"] + " "
                label2 = (edge[1]["interface"].replace("nGigE", "")) + "  " + edge[0][
                    "ip_neighbor"]
                g.add_edge(edge[0]["node"], edge[1]["node"], id=str(id), label=label, label2=label2, width="2.0",
                           color=color, arrowfoot="standard")
                '''
                g.edges[str(id)].add_aditional_label(text="BGP IN "+str(edge[0]["bgp_accepted_prefixes"]),color="#0442a5",position="shead",size="12")
                g.edges[str(id)].add_aditional_label(text="BGP OT " + str(edge[0]["bgp_total_prefixes_advertised"]), color="#933b00",
                                                     position="stail", size="12")
                g.edges[str(id)].add_aditional_label(text="BGP IN " + str(edge[1]["bgp_accepted_prefixes"]), color="#0442a5",

                                                     position="thead", size="12")
                g.edges[str(id)].add_aditional_label(text="BGP OT " + str(edge[1]["bgp_total_prefixes_advertised"]),
                                                    color="#933b00",
            
                                                    position="thead", size="12")
                '''
                edge[0]["device"].set_interfaces_stats(interfaces_index=[edge[0]["interface"]])
                edge[1]["device"].set_interfaces_stats(interfaces_index=[edge[1]["interface"]])
                rate_0 = str(round(edge[0]["device"].interfaces[edge[0]["interface"]].rate_out / 1024 / 1024))
                rate_1 = str(round(edge[1]["device"].interfaces[edge[1]["interface"]].rate_out // 1024 / 1024))
                g.edges[str(id)].add_aditional_label(text="" + rate_0,
                                                     color="#000555",

                                                     position="shead", size="20")
                g.edges[str(id)].add_aditional_label(text="" + rate_1,
                                                     color="#000555",

                                                     position="thead", size="20")

                g.edges[str(id)].add_aditional_label(text="" + str(edge[0]["bgp_description"]),
                                                     color="#780d9b",

                                                     position="head", size="12")
                g.edges[str(id)].add_aditional_label(text=" " + str(edge[1]["bgp_description"]),
                                                     color="#341560",

                                                     position="tail", size="12")

        print(g.get_graph())

    def set_master(self, username, password, logg_name="master"):
        self.master = Master(password=password, username=username, logg_name="master")

    def dict_qos_ipp(self):
        dict_ipp = {}
        for ipp_name, ipp in self.list_ipp.items():
            dict_ipp[ipp_name] = ipp.get_policy_map_interface_rate()
        return dict_ipp

    def read_file(self, filename):
        return tuple(open(filename, 'r'))

    def correct_device_platform(self, devices):
        threads = []
        device_list = []

        for device in devices:
            t = th.Thread(target=device.get_platform)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        for device in devices:
            platform = device.platform
            device = eval(device.platform)(device.ip, device.display_name, self.master)
            device_list.append(device)
            device.platform = platform
            print(device)
        return device_list

    def get_device_list(self, filename):
        device_list = self.read_file(filename=filename)
        devices = []

        for row in device_list:
            row = row.replace("\n", "").split(";")
            device = CiscoIOS(row[0], "ios", self.master)

            devices.append(device)
        return devices

    def excute_methods(self, methods, devices):
        th.Thread()
        ready_devices = []

        for method, variable in methods.items():
            threads = []
            for device in devices:
                method_instantiated = getattr(device, method)
                t = th.Thread(target=method_instantiated)
                t.start()
                threads.append(t)
            for t in threads:
                t.join()

        return devices

    def clean_list_devices(self, devices):

        new_devices = []
        for device in devices:
            if (Claro.check_device_up(device)):
                if (Claro.check_telnet(device) or Claro.check_ssh(device)):
                    new_devices.append(device)
                else:
                    self.not_connected_devices.append(device.ip)
        return new_devices, self.not_connected_devices

    @staticmethod
    def check_device_up(device):

        """
            Returns True if host (str) responds to a ping request.
            Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
            """

        # Ping command count option as function of OS
        param1 = '-n' if system_name().lower() == 'windows' else '-c'
        param2 = '-w' if system_name().lower() == 'windows' else '-W'
        # Building the command. Ex: "ping -c 1 google.com"
        command = ['ping', param2, '200', param1, '1', device.ip]

        # Pinging
        return system_call(command, shell=True) == 0

    @staticmethod
    def check_ssh(device):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((device.ip, 22))
        return result == 0

    @staticmethod
    def check_telnet(device):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((device.ip, 23))
        return result == 0

    def check_device_able_connect(self, device):
        return (self.check_device_up(device=device)) and (
                self.check_ssh(device=device) or self.check_telnet(device=device))

    def adj_report(self, report_name, device_list_filename):

        methods = {"set_mpls_ldp_interfaces": "mpls_ldp_interfaces",
                   "set_pim_interfaces": "pim_interfaces", "set_ip_ospf_interfaces": 'ospf_interfaces'
                   }
        devices = self.get_device_list(filename=device_list_filename)
        devices = self.clean_list_devices(devices=devices)
        devices = self.correct_device_platform(devices=devices)
        ready_devices = self.excute_methods(methods=methods, devices=devices)
        self.save_sql_devices(devices=ready_devices, methods=methods, report_name=report_name)
        self.save_report(report_name)

    def save_sql_devices(self, devices, methods, report_name):
        for device in devices:
            for method, variable in methods.items():
                device.save_report_sql(atribute=variable, report_name=report_name)

    def save_report(self, report_name):
        rows, cursor = self.get_rows_sql_report(report_name=report_name)
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet("prueba")
        rows_skipped = 2
        for colidx, heading in enumerate(cursor.description):
            worksheet.write(rows_skipped, colidx, heading[0])

        # Write rows
        for rowidx, row in enumerate(rows):
            for colindex, col in enumerate(row):
                worksheet.write(rowidx + rows_skipped + 1, colindex, col)
        workbook.save(report_name + '.xls')

    def get_cursor_db(self):
        try:
            conn = pmsql.connect(
                "dbname='" + self.dbname + "' user='" + self.dbuser + "' host='" + self.dbhost + "' password='" + self.dbpassword + "'")
            return conn.cursor()
        except Exception:
            return 0

    def get_rows_sql_report(self, report_name):
        cursor = self.get_cursor_db()
        sql = "select COALESCE( ospf.interface,ldp.interface,pim.interface) as interface, COALESCE(ospf.local_router_ip ,ldp.local_router_ip ,pim.local_router_ip) as ip , * from pim_interfaces as pim full outer join ospf_interfaces as ospf on ((pim .report_name = ospf.report_name) and  (pim.local_router_ip	 =  ospf.local_router_ip) and ( pim.interface= ospf.interface)) full outer join  mpls_ldp_interfaces as ldp on ((ldp.report_name = ospf.report_name) and (ldp.local_router_ip =  ospf.local_router_ip) and ( ldp.interface =  ospf.interface)) WHERE  ldp.report_name='" + report_name + "'"
        cursor.execute(sql)
        rows = cursor.fetchall()
        return rows, cursor

    def ospf_save_excel_adj(self):

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet("1")
        worksheet.write(0, 1, 'network_id')

        rows_skipped = 2
        db_mongo = self.master.connect_mongo()
        ospf_adjs = db_mongo.ospf_adj.find({'$where': "this.interfaces.length > 1"})
        rowidx = 0
        for adj in ospf_adjs:
            rowidx += 1
            colid = 4
            print(rowidx)
            worksheet.write(rowidx, 1, adj['network_id'])
            mtu_compare = None
            mtu_flag_bad = False
            for interface in adj['interfaces']:
                if not mtu_flag_bad:

                    mtu = interface['mtu']
                    for keys, value in interface.items():
                        colid += 1
                        print(str(rowidx) + " : " + str(colid))
                        worksheet.write(rowidx, colid, value)
                    try:
                        mtu_interface = int(mtu)
                    except ValueError as verr:
                        mtu_interface = 0
                        pass  # do job to handle: s does not contain anything convertible to int
                    except Exception as ex:
                        mtu_interface = 0
                        pass  # do job to handle: Exception occurred while converting to int
                    if interface['device_plattform'] == 'CiscoXR':
                        mtu_interface = mtu_interface - 14
                    if mtu_compare is None:
                        mtu_compare = mtu_interface
                    else:
                        mtu_flag_bad = mtu_interface != mtu_compare
            worksheet.write(rowidx, 2, mtu_flag_bad)
            if (mtu_flag_bad):
                print(adj)
        # Write rows

        workbook.save('reporte_prueba3.xls')

    def consulted_devices(self):
        db_mongo = self.master.connect_mongo()
        ospf_devices = db_mongo.ospf_adj.aggregate([{"$unwind": "$interfaces"},
                                                    {"$project": {"interfaces.ip_neighbor": 1}}])
        devices = {}
        for device in ospf_devices:
            devices[device["interfaces"]["ip_neighbor"]] = 1

        pprint(devices)

    def ospf_save_adj(self):

        devices = self.clean_list_devices(self.get_device_list("C:\\Users\\descudero\\Desktop\\listado.csv"))
        devices = self.correct_device_platform(devices=devices)
        methods = {"save_ospf_adjacencies": "test"}
        self.excute_methods(methods, devices)

    def opsf_check_mtu_adjacencies(self):
        db_mongo = self.master.connect_mongo()
        ospf_adjs = db_mongo.ospf_adj.find({'$where': "this.interfaces.length > 1"})
        for adj in ospf_adjs:
            mtu_compare = None
            mtu_flag_bad = False
            for interface in adj['interfaces']:
                if not mtu_flag_bad:
                    mtu = interface['mtu']
                    try:
                        mtu_interface = int(mtu)
                    except ValueError as verr:
                        mtu_interface = 0
                        pass  # do job to handle: s does not contain anything convertible to int
                    except Exception as ex:
                        mtu_interface = 0
                        pass  # do job to handle: Exception occurred while converting to int
                    if interface['device_plattform'] == 'CiscoXR':
                        mtu_interface = mtu_interface - 14
                    if mtu_compare is None:
                        mtu_compare = mtu_interface
                    else:
                        mtu_flag_bad = mtu_interface != mtu_compare
            if (mtu_flag_bad):
                print(adj)

    def asr_mod_inventory(self):
        devices = self.load_devices_csv("host.csv")
        self.excute_methods(devices=devices, methods={"set_inventory": {}, "set_physical_interfaces": {}})
        for device in devices:
            pprint(device.inventory)

    def load_devices_csv(self, filename):
        open_file = open(filename, "r").read()
        devices = []
        for device_line in open_file.split("\n")[1:]:
            device_data = device_line.split(",")
            platform = device_data[4]
            ip = device_data[3]
            hostname = device_data[0]
            device = eval(platform)(ip, hostname, self.master)

            device.platform = platform
            devices.append(device)
        return devices

    def devices_from_network(self, string_network, window=30):
        network = ipaddress.ip_network(string_network)
        hosts = network.hosts()
        host_string_ip = []
        for host in hosts:
            host_string_ip.append(str(host))
        # pprint(host_string_ip)
        # pprint(hosts)
        final_responses = {}
        final_no_responses = {}
        ip_devices = []
        while (len(host_string_ip) > 0):
            if (window > (len(host_string_ip))):
                window = len(host_string_ip)
            responses, no_responses = multi_ping(host_string_ip[0:window - 1], timeout=1, retry=5)
            # pprint(responses)
            if (window == len(host_string_ip)):
                host_string_ip = []
                print("no more hosts")
            else:
                host_string_ip = host_string_ip[window:]
                print("new ping window")
                # pprint(host_string_ip)
            pprint([*responses])
            ip_devices = ip_devices + [*responses]
            final_responses = {**responses, **final_responses}
            devices = []
            for ip in ip_devices:
                device = CiscoIOS(ip, "ios", self.master)
                devices.append(device)
        devices = self.correct_device_platform(devices)
        return devices, ip_devices

    def generate_report_consumption(self, network, filename="test", window=35):
        devices, ipdevices = self.devices_from_network(network, window)
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H%M%S')
        self.excute_methods(devices=devices, methods={"set_all_interfaces": {}, "set_snmp_community": {}})
        interface_data = []
        for device in devices:
            interface_data = interface_data + device.get_interfaces_dict_data()
        self.save_to_excel_list(interface_data, file_name=filename + "_" + timestamp)

"""
    def display_qos_ipp(self):
        vertical_layout = BoxLayout(orientation="vertical")
        #es el layout donde estaran los titulos

        title_layout = BoxLayout(orientation="horizontal",spacing=5)
        title_layout.size_hint = (1, 0.05)
        gray =[0.5,0.50,0.5,0.5]
        title_layout.add_widget(LabelB(text="IPP",bcolor=gray,size_hint_x=0.07))
        title_layout2 = BoxLayout(orientation="horizontal",spacing=2)
        title_in=["BW", "GT IN", "SV IN", "CR IN", "NI IN", "HN IN", "DEFAULT","TOTAL", "%"]
        title_out=["BW", "GT OUT", "SV OUT", "HN OUT", "NI OUT", "NI OUT", "DEFAULT","TOTAL", "%"]
        title_layout2in = BoxLayout(orientation="horizontal",spacing=2)
        title_layout2out = BoxLayout(orientation="horizontal", spacing=2)
        title_layout2.add_widget(LabelB(text="INTER",bcolor=gray,size_hint_x=0.16))
        title_layout2.add_widget(LabelB(text="TAG", bcolor=gray, size_hint_x=0.14))
        for title in title_in:
            title_layout2in.add_widget(LabelB(text=title,bcolor=gray,font_size=12))
        for title in title_out:
            title_layout2out.add_widget(LabelB(text=title,bcolor=gray,font_size=12))
        title_layout2.add_widget(title_layout2in)
        title_layout2.add_widget(title_layout2out)
        title_layout.add_widget(title_layout2)

        all_ipp_layout=BoxLayout(orientation="vertical",spacing=5)
        vertical_layout.add_widget(title_layout)
        vertical_layout.add_widget(all_ipp_layout)

        listLayout={}
        maxsize=0
        maxsize2=0;
        size_interfaces={}
        for key, ipp in self.list_ipp.items():
            ipp.set_internet_interfaces()
            size_interfaces[key]=len(ipp.internet_interfaces)+1
            maxsize2 += size_interfaces[key]

        for key, ipp in self.list_ipp.items():

            #esta es la linea para agregar un ipp
            ipp_layout = BoxLayout(orientation="horizontal",spacing=2)
            ipp_layout.size_hint_x=1 #se le agrega la propiedad full del pafre
            #se crea un label con el nombre del IPP
            ipp_label = LabelB(text=ipp.display_name,bcolor=[0.5, 0.8, 0.2, 0.25])
            #se crea el hint de 5% de ancho
            ipp_label.size_hint = (0.07,1)
            #se retorna un box layout del ipp
            policy_layout_ipp=ipp.get_kivy_policy_rate()
            #Se le agrega un hint de 95% de el ancho del padre
            policy_layout_ipp.size_hint_x=.95

            #se agrega el label al layout del ipp
            ipp_layout.add_widget(ipp_label)
            #se aagrega el layout por interfaz del policy
            ipp_layout.add_widget(policy_layout_ipp)
            ipp_layout.size_hint=(1,size_interfaces[key]/maxsize2)
            all_ipp_layout.add_widget(ipp_layout)


            #se agrega al layout principal

        return vertical_layout
"""
