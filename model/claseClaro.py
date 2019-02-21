import socket
from platform import system as system_name  # Returns the system/OS name
from subprocess import call   as system_call  # Execute a shell command
import datetime
import subprocess
from multiping import multi_ping
import threading as th
from lib import pyyed
import shelve
import time
import os, sys
import socket
import random
from struct import pack, unpack
from datetime import datetime as dt
from model.ospf_database import ospf_database
import yaml
from tools import logged
from flask import jsonify

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto.rfc1902 import Integer, IpAddress, OctetString

import psycopg2 as pmsql
import xlwt

from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR

from pprint import pprint
import ipaddress
import os


@logged
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

    def ospf_topology_vs(self, ip_seed_router, process_id='1', area='0', shelve_name="test_ospf",
                         from_shelve=False):
        self.verbose.warning(f"shelve_name {shelve_name}")
        if from_shelve:
            if os.path.isfile(f"{shelve_name}"):
                with shelve.open(shelve_name) as sh:
                    dict_ospf = sh["db"]
                    return dict_ospf
            else:
                return {"label": "no_data_in_date"}
        else:

            ospf_db = ospf_database(ip_seed_router=ip_seed_router, isp=self, process_id=process_id, area=area)
            with shelve.open(shelve_name) as sh:
                dict_ospf = ospf_db.get_vs()
                sh.clear()
                sh["db"] = dict_ospf
                sh.close()
                return dict_ospf



    def ospf_topology(self, ip_seed_router, process_id='1', area='0', filename="pruebayed"):
        ospf_db = ospf_database(ip_seed_router=ip_seed_router, isp=self, process_id=process_id, area=area)
        ospf_db.get_yed_file(filename=filename)

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
        self.excute_methods(methods=methods, devices=cisco_sources.values())

        for tunnel_instance, tunnel in mpls_te_data.items():
            if (tunnel["source_ip"] not in cisco_sources):
                cisco_sources[tunnel["source_ip"]] = CiscoIOS(master=self.master, ip=tunnel["source_ip"],
                                                              display_name=tunnel["source_ip"])
            device = cisco_sources[tunnel["source_ip"]]
            service_instance_data = device.get_service_instance_by_tunnel_id(tunnel_id=tunnel["tunnel_id"])
            if (service_instance_data != "null"):

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

                if service_instances_vfi:
                    for service_instance_data in service_instances_vfi:
                        tunnel["root_interface"] += service_instance_data["interface"] + " ! "
                        tunnel["root_service_instance"] += service_instance_data["service_instance"] + " ! "
                        tunnel["root_description"] += service_instance_data["description"] + " ! "
                        tunnel["root_dot1q"] += service_instance_data["dot1q"] + " ! "

        # pprint(mpls_te_data)

        self.save_to_excel_dict(mpls_te_data, filename)

    def dict_to_list(self, dict_input):

        return dict_input.values()

    def save_to_excel_dict(self, dictionay_data, file_name):
        data_list = self.dict_to_list(dict_input=dictionay_data)
        self.save_to_excel_list(data_list, file_name)

    def save_to_excel_list(self, list_data, file_name):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet("data")
        rows_skipped = 0

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
            hostname = device.hostname
            device = eval(device.platform)(device.ip, device.display_name, self.master)
            device_list.append(device)
            device.platform = platform
            device.hostname = hostname
        return device_list

    def get_device_list(self, filename):
        device_list = self.read_file(filename=filename)
        devices = []

        for row in device_list:
            row = row.replace("\n", "").split(";")
            device = CiscoIOS(row[0], "ios", self.master)

            devices.append(device)
        return devices

    def do_uni_methods(self, methods, devices, thread_window=100, dict_kwargs={}):
        th.Thread()
        threads = []

        for device in devices:
            for method, variable in methods.items():
                self.dev.info("dev {0} excute method {1}".format(device, method))
                self.verbose.info("dev {0} excute method {1}".format(device, method))
                try:
                    if (len(threads) < thread_window):
                        method_instantiated = getattr(device, method)
                        if (device.ip in dict_kwargs):
                            t = th.Thread(target=method_instantiated, kwargs=dict_kwargs[device.ip])
                        else:
                            t = th.Thread(target=method_instantiated)
                        t.start()
                        threads.append(t)
                    else:
                        self.dev.info("excute_methods: Window join ")
                        self.verbose.info("excute_methods: Window join ")
                        for t in threads:
                            t.join()
                        threads = []

                except Exception as e:
                    self.verbose.warning("dev {0} excute method {1} error {2}".format(device, method, repr(e)))
        for t in threads:
            t.join()

        return devices

    def excute_methods(self, methods, devices, thread_window=100, dict_kwargs={}):
        th.Thread()
        threads = []
        for method, variable in methods.items():

            for device in devices:
                self.dev.info("dev {0} excute method {1}".format(device, method))
                self.verbose.info("dev {0} excute method {1}".format(device, method))
                try:
                    if (len(threads) < thread_window):
                        method_instantiated = getattr(device, method)
                        if (device.ip in dict_kwargs):
                            t = th.Thread(target=method_instantiated, kwargs=dict_kwargs[device.ip])
                        else:
                            t = th.Thread(target=method_instantiated)
                        t.start()
                        threads.append(t)
                    else:
                        self.dev.info("excute_methods: Window join ")
                        self.verbose.info("excute_methods: Window join ")
                        for t in threads:
                            t.join()
                        threads = []

                except Exception as e:
                    self.verbose.warning("dev {0} excute method {1} error {2}".format(device, method, repr(e)))
        for t in threads:
            t.join()

        return devices

    def clean_list_devices(self, devices):

        new_devices = []

        return [device for device in devices if device.check_able_connect()]

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

    def devices_from_ip_list(self, list_devices_ip):
        devices = []
        for ip in list_devices_ip:
            device = CiscoIOS(ip, "ios", self.master)
            devices.append(device)
        return devices

    def devices_from_network(self, string_network, window=30):
        network = ipaddress.ip_network(string_network)
        hosts = network.hosts()
        host_string_ip = []
        for host in hosts:
            host_string_ip.append(str(host))
        final_responses = {}
        final_no_responses = {}
        ip_devices = []
        while (len(host_string_ip) > 0):
            if (window > (len(host_string_ip))):
                window = len(host_string_ip)
            responses, no_responses = multi_ping(host_string_ip[0:window - 1], timeout=1, retry=2)
            # pprint(responses)
            if (window == len(host_string_ip)):
                host_string_ip = []
            else:
                host_string_ip = host_string_ip[window:]
                # pprint(host_string_ip)
            ip_devices = ip_devices + [*responses]
            self.verbose.info("responses {0}".format(len(str(responses.keys()))))
            final_responses = {**responses, **final_responses}
        devices = []
        self.logger_connection.info("Devices up {0} in net {1}".format(len(ip_devices), string_network))
        for ip in ip_devices:
            device = CiscoIOS(ip, "ios", self.master)
            devices.append(device)
        self.verbose.debug("Devices created {0}".format(len(devices)))
        devices = self.correct_device_platform(devices)
        self.verbose.debug("devices corrected {0}".format(len(devices)))
        return devices, ip_devices

    def generate_report_consumption(self, network, filename="test", window=35):
        devices, ipdevices = self.devices_from_network(network, window)
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H%M%S')
        self.excute_methods(devices=devices, methods={"set_interfaces": {}})
        interface_data = []
        for device in devices:
            interface_data = interface_data + device.get_interfaces_dict_data()
        self.save_to_excel_list(interface_data, file_name=filename + "_" + timestamp)

    def get_service_instance_with_pseudowires(self, devices):
        final_list = []

        for device in devices:
            final_list.extend([{**si_data, "parent_device_ip": device.ip} for si_data in
                               device.get_vfis_interface_per_service_instance().values()])

        return final_list

    def save_interfaces_state_db(self, template='internet_ufinet.yml'):
        template_data = yaml.load(open(template).read())
        interfaces = []
        methods = {'set_interfaces': {}}
        for device_group, data in template_data.items():
            devices = self.devices_from_ip_list(data['devices'])
            devices = self.correct_device_platform(devices)
            self.excute_methods(methods=methods, devices=devices)
            for device in devices:
                for filter in data['filters']:
                    interfaces += device.get_interfaces_filtered(filters=filter)
        for interface in interfaces:
            interface.save_state()


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
