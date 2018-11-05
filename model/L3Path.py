import threading
import time

import xlwt

from model.CiscoIOS import CiscoIOS
from model.IpRoute import IpRoute

'''
L3Path. El objetivo de sta clase es crear una secuencia de equipos, rutas y interfaces por la cual
cursa el trafico de cierta ruta L3
la idea es tener una estructura de datos recursiva para formar un arbol de ruta en 1 sentido.

'''


class L3Path:
    def __init__(self, network_model, device_ip, prefix, vrf="null", parent="null"):
        self.state = "init"
        self.network_model = network_model
        self.device_ip = device_ip
        self.device = CiscoIOS(self.device_ip, self.device_ip, self.network_model.master)
        self.prefix = prefix
        self.ip_route = "null"
        self.vrf = vrf
        self.parent_path = parent
        self.next_hops = {}
        self.incoming_interfaces = []

    def init_path(self):
        if self.network_model.check_device_able_connect(self.device):
            self.device = self.network_model.correct_device_platform([self.device])[0]
            if (type(self.device) is str):
                self.state = "dead_end_unable_connect"
            else:
                self.device.diplay_name = self.device.hostname
                self.state = "device_ready"
        else:
            self.state = "dead_end_unable_connect"

        return self.state

    def set_paths(self):
        self.set_reverse_path()
        connection = self.device.connect()
        ip_route = IpRoute.get_instance_route(connection=connection, parent_device=self.device, prefix=self.prefix,
                                              vrf=self.vrf)
        while ip_route.protocol == "bgp":
            ip_route = IpRoute.get_instance_route(connection=connection, parent_device=self.device,
                                                  prefix=ip_route["paths"][0]["next_hop"], vrf="null")

        if (ip_route.has_paths()):
            if (ip_route.protocol != "ospf"):
                self.state = "dead_end_" + self.protocol
            else:
                self.device.set_ip_ospf_interfaces()
                # print(self.device.ospf_interfaces)
                for path in ip_route.paths:
                    if (path["out_interface"] in self.device.ospf_interfaces):
                        ip_ospf_id_next_hop = self.device.ospf_interfaces[path["out_interface"]]["ospf_neighbor"]
                        if (ip_ospf_id_next_hop != "0.0.0.0"):
                            if self.check_path_in_parent(ip_ospf_id_next_hop) == False:
                                if self.check_path_in_self(ip_ospf_id_next_hop) == False:
                                    l3path = L3Path(self.network_model, ip_ospf_id_next_hop, self.prefix, vrf="null",
                                                    parent=self)
                                    self.next_hops[ip_ospf_id_next_hop] = {"L3Path": l3path,
                                                                           "interfaces": [path["out_interface"]]}
                                    self.state = "has_next_hop"
                                else:
                                    self.next_hops[ip_ospf_id_next_hop]["interfaces"].append(path["out_interface"])
                            else:
                                self.state = "dead_end_already_in_path"
                        else:
                            self.state = "dead_end_no_ospf_neighbor"

    def search_recursive_path_route(self):
        self.init_path()
        if (self.state == "device_ready"):
            self.set_paths()
            # print(self.next_hops)
            for ip, next_hops in self.next_hops.items():
                next_hops["L3Path"].search_recursive_path_route()

    def check_path_in_self(self, ip_next_hop):
        # print("adenntro del check")
        return ip_next_hop in self.next_hops

    def check_path_in_parent(self, ip_next_hop):
        # print("adenntro del padre")
        if (self.parent_path != "null"):
            return self.parent_path.check_path_all(ip_next_hop)
        else:
            return False

    def check_path_all(self, ip_next_hop):

        return self.check_path_in_self(ip_next_hop=ip_next_hop) or self.check_path_in_parent(ip_next_hop=ip_next_hop)

    def string_path(self, hop=0):
        hop += 1
        output = ""
        if (hop == 1):
            output += "Prefix search " + "  " + str(self.prefix) + "\n"
        output += "******hop count " + str(hop) + "*******\n"

        output += "Device ip " + self.device.ip + " " + self.state + "\n"
        output += "Incoming Interfaces" + "\n"
        for incoming_interface in self.incoming_interfaces:
            output += incoming_interface + "||"
        output += "\n"
        output += "Outgoing paths \n"
        for ip_next_hop, path in self.next_hops.items():
            output += "next hop path " + ip_next_hop + "\n"
            output += "out interfaces: "

            for interface in path["interfaces"]:
                output += interface + "||"
            output += "\n"
            output += path["L3Path"].string_path(hop)

        return output

    def set_reverse_path(self):
        if (self.parent_path != "null"):
            connection = self.device.connect()
            ip_route = IpRoute.get_instance_route(connection=connection, parent_device=self.device,
                                                  prefix=self.parent_path.device.ip,
                                                  vrf=self.vrf)
            for path in ip_route.paths:
                self.incoming_interfaces.append(path["out_interface"])
            return connection
        return "null"

    def set_method_recursive_thread(self, method, threads=[], kwargs={}):

        set_method_instantiated = getattr(self, method)
        t = threading.Thread(target=set_method_instantiated, kwargs=kwargs)
        t.start()
        threads.append(t)
        for ip_next_hop, path in self.next_hops.items():
            path["L3Path"].set_method_recursive_thread(method, threads, kwargs)

        if self.parent_path == "null":
            for t in threads:
                t.join()
        return 1

    def set_interfaces_stats(self):
        interfaces = []
        if self.state != "dead_end_unable_connect":
            interfaces = interfaces + self.incoming_interfaces
            for ip_next_hop, path in self.next_hops.items():
                interfaces = interfaces + path["interfaces"]
            self.device.set_interfaces_stats(interfaces_index=interfaces)
        return len(interfaces)

    def present_interfaces_stats(self):
        interfaces = []
        output = ""
        if self.state != "dead_end_unable_connect":
            output = "////////////////////////////////\n"
            output += " HOP " + self.device.ip + " Incoming interface \n"
            output += self.device.get_interfaces_stats(interfaces_index=self.incoming_interfaces)
            output += " output interfaces \n"
            for ip_next_hop, path in self.next_hops.items():
                output += self.device.get_interfaces_stats(interfaces_index=path["interfaces"])

        return output

    def present_method_recursive(self, method):
        get_method_instantiated = getattr(self, method)
        output = get_method_instantiated()
        for ip_next_hop, path in self.next_hops.items():
            output += path["L3Path"].present_method_recursive(method)
        return output

    def get_interfaces_stats(self):
        self.set_method_recursive_thread("set_interfaces_stats")
        output = self.present_method_recursive("present_interfaces_stats")
        return output

    def set_log(self, filter=""):

        self.device.set_log(filter)

    def get_log(self, filter=""):
        self.set_method_recursive_thread(method="set_log", kwargs={"filter": filter})
        self.present_log_recursive()

    def present_log_recursive(self, logs={}, save_xls=True):
        logs[self.device.ip] = self.device.get_log()

        for ip_next_hop, path in self.next_hops.items():
            path["L3Path"].present_log_recursive(logs, save_xls)
        # print(logs.keys())
        if (save_xls and self.parent_path == "null"):
            file_name = "show logg path " + self.prefix + str(time.strftime(" %Y_%m_%d_%H_%M_%S")) + ".xls"
            print("saved_log to:" + file_name)
            workbook = xlwt.Workbook()
            for sheet, log in logs.items():
                worksheet = workbook.add_sheet(sheetname=sheet)
                rows_skipped = 2

                # Write rows
                for rowidx, row in enumerate(log):
                    worksheet.write(rowidx + rows_skipped + 1, 1, row)
            workbook.save(filename_or_stream=file_name)

    '''

    descripcion
    rate
    mtu
    errors
    logg
    potencias
    tipo modulo
    ldp
    policy map
    IP OSPF cost
    '''
