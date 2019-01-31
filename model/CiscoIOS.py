import ipaddress
import re
import shelve
import sqlite3 as sql
from pprint import pprint
import psycopg2 as pmsql
from multiping import multi_ping
from netmiko import ConnectHandler
from netmiko import NetMikoAuthenticationException
from netmiko import NetMikoTimeoutException
from paramiko import AuthenticationException
from paramiko import SSHException
from pysnmp.entity.rfc3413.oneliner import cmdgen

import lib.pyyed as pyyed
from model.BaseDevice import BaseDevice as Parent
from model.CiscoPart import CiscoPart
from model.InterfaceUfinet import InterfaceUfinet
from tools import normalize_interface_name, logged, replace
from lib.snmp_helper import *
from model.BridgeDomain import BridgeDomain
from model.IpExplicitPath import IpExplicitPath
from model.MplsTeTunnel import MplsTeTunnel
import sys


@logged
class CiscoIOS(Parent):
    images = {"GUATEMALA": "_GT",
              "El_SALVADOR": "_SV",
              "HONDURAS": "_HN",
              "NICARAGUA": "_NC",
              "COSTA_RICA": "_CR",
              "PANAMA": "_PN", "COLOMBIA": "_CO",
              "USA": "_US", "ARGENTINA": "_AR", "CHILE": "_CL",

              }

    def __init__(self, ip, display_name, master, platform="CiscoIOS", gateway="null"):
        edge_step = 41
        self.yed_edges_points = {"N": [(str(x), "125") for x in range(-135, 136, edge_step)],
                                 "S": [(str(x), "-125") for x in range(-135, 136, edge_step)],
                                 "E": [("125", str(y)) for y in range(-135, 136, edge_step)],
                                 "W": [("-125", str(y)) for y in range(136, -136, -edge_step)]}

        super().__init__(ip, display_name, master, platform, gateway)
        self.pseudo_wire_class = dict()
        self.mpls_te_tunnels = dict()
        self.service_instances = dict()
        self.template_type_pseudowires = dict()
        self.config = ""
        self.pseudowires = dict()
        self.static_routes = dict()
        self.inventory = dict()
        self.platform = platform
        self.community = ""
        self.interfaces_ip = dict()
        self.ldp_neighbors = dict()
        self.mpls_ldp_interfaces = dict()
        self.ospf_interfaces = dict()
        self.bridge_domains = dict()
        self.add_p2p_ospf = dict()
        self.dev.debug("device {0} INIT".format(self.ip))
        self.device_type = "cisco_ios_"
        self.uid = 0

    def add_p2p_ospf(self, p2p, p2p_ospf):

        self.add_p2p_ospf[p2p.network_id] = {"p2p": p2p, "neighbor": p2p_ospf}

    def send_command(self, connection, command="", pattern="#", read=True, timeout=4):

        '''
           metodo: send_comand
               Parametros:
                   Connection (connection): es un objeto connection creado con el metodo "connect"
                   command (string): es la sentencia que se le envia al equipo
                   pattern(string): es el patron que busca antes de seguir esperando por el comando y regresa data desde
                   despues del comando hasta el pattern. el default es #
                   read (boolean), no se utiliza
                   timeout(int), es un factor que se utiliza para retrazar la espera del comando, se utiliza cuando
                   son comandos o equipos muy lentos

               retorno (string): regresa el output del comando sin el comando.

           '''

        output = ""
        retry_counter = 0
        while output == "" and retry_counter < 1:
            self.logger_connection.info(" {0} about to sen command {1} RC {2}".format(self.ip, command, retry_counter))
            retry_counter += 1
            try:
                output = connection.send_command(command_string=command, delay_factor=timeout,
                                                 expect_string=pattern, max_loops=55550)
                self.logger_connection.debug(" {0}  {1} output {2} ".format(self.ip, command, output))
            except (OSError, AttributeError) as e:
                self.logger_connection.error(
                    " {0} s error unable to send command {1} error {2}".format(self.ip, command, repr(e)))

                output = ""
        if output == "":
            self.logger_connection.error(" {0} no output {1}".format(self.ip, command))
        return output

    def internet_validation_arp(self, test_name, vrf):
        test_ping = shelve.open(test_name + self.display_name)
        if "responses" in test_ping:
            test_ping["responses"]
            responses, no_responses = multi_ping(test_ping["responses"].keys(), timeout=3, retry=2,
                                                 ignore_lookup_errors=True)
            no_responses2 = no_responses
            test_ping["test_no_responses"] = no_responses

            for i in range(0, 5):
                if len(no_responses2) > 0:
                    responses2, no_responses = multi_ping(no_responses2, timeout=3, retry=1, ignore_lookup_errors=True)
                    responses = {**responses, **responses2}
                    no_responses2 = no_responses
                else:
                    i = 3
            test_ping.close()
            return responses, no_responses

        else:
            responses, no_responses = self.test_multiping_arp(vrf=vrf)
            test_ping["responses"] = responses
            test_ping["no_responses"] = no_responses
            test_ping.close()
            return responses, no_responses

    def test_multiping_arp(self, vrf="default"):
        self.set_arp_list(vrf=vrf)

        # for index in range(0,len(self.arp_list.keys()),step=30)
        #   end = len(self.arp_list.keys())
        # responses, no_responses = multi_ping(dest_addrs=self.arp_list.keys()[step], timeout=3, retry=5,
        #                                    ignore_lookup_errors=True)

        # return responses, no_responses

    def get_service_instance_data(self, interface, service_instance):
        try:
            return self.service_instances[interface + ":" + service_instance]
        except:
            return 'null'

    def set_pseudo_wire_class(self):
        # todo change to txtfsm
        command = "show run | s pseudowire-class"
        connection = self.connect()
        output = self.send_command(command=command, connection=connection)
        connection.disconnect()
        for pw_class in output.split("pseudowire-class ")[1:]:

            lines = pw_class.split("\n")
            data = dict()
            data["encapsulation"] = lines[1].replace(" encapsulation ", "")

            if len(lines) > 2:
                if lines[2].find("Tunnel"):
                    data["interface"] = lines[2].replace(" preferred-path interface ", "").replace(" ", "").replace(
                        "disable-fallback", "")
            self.pseudo_wire_class[lines[0]] = data

    def set_mpls_te_tunnels(self):
        # todo change to textfsm template, template listo solo falta el methodo
        # todo create mpls te tunnel
        command = "show mpls traffic-eng tunnels detail"
        template = "show mpls traffic-eng tunnels detail.template"
        te = self.send_command_and_parse(template_name=template,
                                         command=command)

        mpls_te_tunnels = {tunnel['tunnel']: tunnel for tunnel in te}
        self.mpls_te_tunnels = {tunnel['tunnel']: MplsTeTunnel(txtfsmdata=tunnel, parent=self) for tunnel in te}

        return mpls_te_tunnels

    def set_service_instances(self):
        # todo change to textfsm template

        command = "show ethernet service instance detail"
        template = "show ethernet service instance detail ios.template"
        service_instances = self.send_command_and_parse(template_name=template,
                                                        command=command)
        self.service_instances = {normalize_interface_name(row["interface"]) + ":" + row["id"]: row
                                  for row in service_instances}

        return self.service_instances

    def get_template_by_tunnel_id(self, tunnel_id):
        for name, template in self.template_type_pseudowires.items():
            if (template["interface"] == "Tunnel" + str(tunnel_id)):
                return name
        return "null"

    def get_vfi_by_template(self, template_name):

        for name, vfi in self.vfis.items():
            for pseudowire in vfi["pseudowires"]:
                if pseudowire["template"] == template_name:
                    return name
        return "null"

    def get_interfaces_instance_by_vfi(self, vfi):

        for name, bridge in self.bridge_domains.items():
            if "vfi" in bridge:
                if (bridge["vfi"] == vfi):
                    return bridge["interfaces"]
        return []

    def get_service_instance_by_interfaces(self, interfaces):

        return [self.get_service_instance_data(interface["interface"], interface["service_instance"])
                for interface in interfaces]

    def get_service_instance_by_tunnel_id_vfi(self, tunnel_id):
        template = self.get_template_by_tunnel_id(tunnel_id=tunnel_id)
        vfi = self.get_vfi_by_template(template_name=template)
        interfaces = self.get_interfaces_instance_by_vfi(vfi=vfi)
        service_instances = self.get_service_instance_by_interfaces(interfaces)
        return service_instances

    def set_template_type_pseudowires(self, ):
        # todo change to textfsm
        command = "show run | s template type"
        connection = self.connect()
        output = self.send_command(command=command, connection=connection)
        connection.disconnect()
        for template in output.split("template type pseudowire")[1:]:
            data = {}
            lines = template.split("\n")
            data["name"] = lines[0].replace(" ", "")
            if len(lines) > 2:
                data["interface"] = lines[2].replace(" preferred-path interface", "").replace(" ", "")
            else:
                data["interface"] = "null"
            self.template_type_pseudowires[data["name"]] = data

    def set_bridge_domains(self):
        # todo change to textfsm
        list_bridge = self.send_command_and_parse(template_name="show bridge-domain ios.template",
                                                  command="show bridge-domain")
        list_bridge_vfi = self.send_command_and_parse(template_name="show bridge-domain vfi ios.template",
                                                      command="show bridge-domain")
        self.bridge_domains = {}
        for interface_bridge in list_bridge:
            index_bd = interface_bridge["bride_domain"]
            if index_bd not in self.bridge_domains:
                self.bridge_domains[index_bd] = BridgeDomain(id_bd=index_bd, parent_device=self)
                self.bridge_domains[index_bd].add_interfaces(interface_bridge)
            else:
                self.bridge_domains[index_bd].add_interfaces(interface_bridge)

        for interface_bridge in list_bridge_vfi:
            index_bd = interface_bridge["bride_domain"]
            if index_bd not in self.bridge_domains:
                self.bridge_domains[index_bd] = BridgeDomain(id_bd=index_bd, parent_device=self)
                self.bridge_domains[index_bd].add_vfi(interface_bridge)
            else:
                self.bridge_domains[index_bd].add_vfi(interface_bridge)

    def set_pseudowires(self):

        output = self.send_command_and_parse(template_name="show mpls l2transport vc detail ios.template",
                                             command="show mpls l2transport vc detail")
        self.pseudowires = {row["vc_id"]: row for row in output}

        return self.pseudowires

    def get_pw_class_by_tunnel_id(self, tunnel_id):
        for name, pw_class in self.pseudo_wire_class.items():
            if pw_class["interface"] == "Tunnel" + str(tunnel_id):
                return name

    def get_pseudowire_by_pw_class(self, pw_class):

        for id, pseudowire in self.pseudowires.items():
            if ("pw_class" in pseudowire):
                if (pseudowire["pw_class"] == pw_class):
                    return pseudowire

    def get_service_instance_by_pseudowire(self, pseudowire):

        return self.get_service_instance_data(pseudowire["interface"], service_instance=pseudowire["service_instance"])

    def get_service_instance_by_tunnel_id(self, tunnel_id):
        if (not hasattr(self, 'service_instances')):
            print(self.ip + " set_service_intances ")
            self.set_service_instances()

            # print(self.service_instances.keys())
        if (not hasattr(self, 'pseudo_wire_class')):
            print(self.ip + " pseudo wires class ")
            self.set_pseudo_wire_class()
        if (not hasattr(self, 'pseudowires')):
            print(self.ip + " set_pseudorires ")
            self.set_pseudowires()
        try:
            pw_class = self.get_pw_class_by_tunnel_id(tunnel_id=tunnel_id)
            pseudowire = self.get_pseudowire_by_pw_class(pw_class=pw_class)
            service_instance = self.get_service_instance_by_pseudowire(pseudowire=pseudowire)
        except:
            service_instance = "null"
        return service_instance

    def set_arp_list(self, vrf="default"):
        command = "show ip arp "
        command += (" vrf " + vrf + " ") if vrf != "default" else " "
        command += "  | e plete"
        self.connected_routes = {}

        connection = self.connect()
        output = self.send_command(connection=connection, command=command)
        list_arp_entries = {}
        for line in output.split("\n")[1:]:
            arp_info = {"ip": "0.0.0.0", "time": "-", "mac": "0000.0000.0000", "source": "Interface",
                        "interface": "null"}

            splitline = re.sub(" +", " ", line).split(" ")
            try:
                arp_info["ip"] = splitline[1]
                arp_info["time"] = splitline[2]
                arp_info["mac"] = splitline[3]
                arp_info["source"] = "Dynamic" if arp_info["time"] != "-" else "Interface"
                arp_info["interface"] = splitline[5]
                list_arp_entries[arp_info["ip"]] = arp_info
            except Exception:
                # print(line)
                # print(splitline)
                pass
        self.arp_list = list_arp_entries
        return self.arp_list

    def create_file_nagios_arp(self, vrf="default"):
        arp_dict = self.set_arp_list(vrf=vrf)
        output = ""

        for ip, host in arp_dict.items():
            host_string = "define host {\n"
            host_string += "\tuse\tgeneric-switch\n"
            host_string += "\thost_name\t" + ip + "\n"
            host_string += "\talias\t" + ip + "\n"
            host_string += "\taddress\t" + ip + "\n"
            host_string += "}\n\n"

            host_string += "define service {\n"
            host_string += "\tuse\tlocal-service\n"
            host_string += "\thost_name\t" + ip + "\n"
            host_string += "\tservice_description\tPING\n"
            host_string += "\theck_command\tcheck_ping!100.0,20%!500.0,60%\n"
            host_string += "}\n\n"
            output += host_string
        print(output)

    def set_coneccted_routes(self, vrf="default"):

        command = "show ip route "
        command += (" vrf " + vrf + " ") if vrf != "default" else " "
        command += " connected | i C"
        self.connected_routes = {}

        connection = self.connect()
        output = self.send_command(connection=connection, command=command)
        connection.disconnect()
        for line in output.split("\n")[2:-1]:
            split_line = line.replace("C        ", "").replace(" is directly connected", "").split(',')

            self.connected_routes[split_line[0]] = split_line[1]

    def get_interface_route(self, address, connection="none", vrf="default"):
        command = "show ip route "
        command += (" vrf " + vrf + " ") if vrf != "default" else " "
        command += address

        if connection == "none":
            connection = self.connect()
        output = self.send_command(connection=connection, command=command)
        connection.disconnect()
        if (output.find("directly connected, via") > -1):
            interface = normalize_interface_name(
                output.split("directly connected, via")[1].split("\n")[0].replace(" ", ""))
        else:

            interface = "not conected"
            next_hop = output.split("Routing Descriptor Blocks\n")[1].split("\n")[0].split(",")[0].replace(" ", "")

            return self.get_interface_route(address=next_hop, connection=connection, vrf=vrf)
        network = output.split("Routing entry for ")[1].split("\n")[0].replace(" ", "")
        return network, interface

    def get_interfaces_address(self, list_address, vrf="default"):
        prefix_interface = {}
        connection = self.connect()
        for address in list_address:
            network, interface = self.get_interface_route(address=address, connection=connection, vrf=vrf)
            prefix_interface[address] = {"interface": interface, "network": network}
        self.prefix_per_interface = prefix_interface
        return prefix_interface

    def connect(self, username_pattern='username', password_pattern="password", pattern="#", device_type="cisco_ios_"):
        self.logger_connection.info("Start of connection {0}".format(self.ip))
        '''
           Metodo : connect
               Parametros:
                   username_pattern(string),default ('username'): es el patron para el reconocimiento
                   de cuando ingresar el usuario
                   password_pattern(string) default ('password'): es el patron para el reconocimiento
                   de cuando ingresar el password
                   pattern(string),default(#): es el patron que se utiliza para reconocer cuando se termina
                   de completar un comando

               retorno (ConnectHandler): regresa un objeto ConnectHandler, con la sesion establecia
                                        o regresa un string "null"

                Algoritmo en pseudo codigo.
                    intenta conectarse en el device_type "cisco_ios_telnet"
                    si lo logra
                        retorna connexion
                    si no lo logra
                    intenta conectarse en el device_type "cisco_ios_ssh"
                        retorna connexion
                    si no lo logra
                        retorna error y el objeto como string "null"
        '''
        connection = ""

        retry_counter = 0

        if not hasattr(self, "jump_gateway"):
            while type(connection) is str and retry_counter < 2:
                retry_counter += 1
                self.verbose.warning("connect {0} RC {1}".format(self.ip, str(retry_counter)))
                try:
                    connection = ConnectHandler(device_type=self.device_type + "ssh"
                                                , ip=self.ip,
                                                username=self.master.username,
                                                password=self.master.password)

                except (
                        AuthenticationException, NetMikoTimeoutException, EOFError, SSHException,
                        ConnectionAbortedError,
                        ValueError, ConnectionRefusedError) as e:
                    self.logger_connection.warning(
                        "UNABLE TO CONNECT  SSH {0} ERROR {1}".format(self.ip, str(repr(e))))
                    try:
                        connection = ConnectHandler(device_type=self.device_type + "telnet",
                                                    ip=self.ip, username=self.master.username,
                                                    password=self.master.password)

                    except (NetMikoAuthenticationException, SSHException, EOFError, ConnectionAbortedError, ValueError,
                            ConnectionRefusedError) as e:
                        self.logger_connection.warning(
                            "UNABLE TO CONNECT  TELNET {0} ERROR {1}".format(self.ip, str(repr(e))))

        else:
            # device has to hop another device
            gateway = CiscoIOS(self.jump_gateway["ip"], "gateway", self.master)
            connection = gateway.connect()
            command = "telnet " + self.ip + "\n"
            command += self.master.username + "\n"
            command += self.master.password + "\n"
            gateway.send_command(connection, command, pattern='name:')
            if not connection == "":
                self.logger_connection.info("CONNECTED {0} VIA GTW {1}".format(self.ip, str(gateway)))
            else:
                self.logger_connection.warning("UNABLE TO CONNECT {0}  VIA GTW {1}".format(self.ip, str(gateway)))
        if connection != "":
            self.logger_connection.info("Connected {0} via {1} ".format(self.ip, repr(connection)))

        self.verbose.debug(" {ip} Connection created {connection} ".format(ip=self.ip, connection=connection))
        if type(connection) is str:
            self.verbose.critical(" {ip} unable to connect  ".format(ip=self.ip))
        return connection

    def set_hostname(self, connection, command_host="show run | i hostname"):
        '''
              methodo: set_hotname

                  parametros:
                      connection(ConnectHandler): conneccion al equipo
                      command_host(string) default ("show run | i hostname"): es el string que se define
                      para obtener el hostname del equipo en 1 linea
                  retorno:
                      si se obtiee el hostname, string con el hostname del equipo
                      no se obtine el hostname, string "#"

          '''
        self.set_snmp_community()

    def set_config(self, command="show config"):
        """
        metodo set_config
            :param command (string) default ("show config"): es el comando que muestra la configuracion
            guardada del equipo generalmente es mas rapido lanzar este comando que un show running-config
            :return: la configuracion guardada del equipo

            :pseudocodigo:
                se conecta a equipo
                envia comando "show config" o el paramentro command
                asigna el valor de self.config
                retorna el valor de self.config
        """
        connection = self.connect()
        self.config = self.send_command(connection, command, self.hostname, timeout=10)

        return self.config

    def setActualConfig(self, Acommand="show run"):
        """
               metodo set_config
                   :param command (string) default ("show running"): es el comando que muestra la configuracion
                   utilizando el equipo
                   :return: la configuracion actual del equipo

                   :pseudocodigo:
                       se conecta a equipo
                       envia comando "show running" o el paramentro command
                       asigna el valor de self.config
                       retorna el valor de self.config
               """
        connection = self.connect()
        self.config = self.send_command(connection, Acommand, self.hostname, timeout=10)
        self.close(connection)
        return self.config

    def set_ospf_neighbors(self):
        pass

    def set_ospf_database(self, process):
        command = "show ip ospf " + process + " database router topology"
        connection = self.connect()
        output = self.send_command(connection, command, self.hostname, timeout=10)
        areas = output.split("Router Link States (")[1:]
        database = {}
        for area in areas:
            area_id = area.split("\n")[0].replace(")", "").replace("Area", "").replace(" ", "")

            area_data = {}
            lsas = area.split("LS age:")[1:]
            for lsa in lsas:
                router = lsa.split("\n")[3].replace("Link State ID: ", "").replace(" ", "")
                links = lsa.split("Link connected to: ")[1:]
                stubs = {}
                point_to_point = {}
                for link in links:
                    lines = link.split("\n")
                    if (lines[0].find("Stub Network") > -1):
                        stub = {}
                        stub["subnet"] = lines[1].split(":")[1].replace(" ", "")
                        stub["mask"] = lines[2].split(":")[1].replace(" ", "")
                        stub["metric"] = lines[4].split(":")[1].replace(" ", "")
                        stubs[stub["subnet"]] = stub
                    else:
                        if (lines[0].find("point-to-point")):
                            p2p = {}
                            p2p["neighbor_ip"] = lines[1].split(":")[1].replace(" ", "")
                            p2p["interface_ip"] = lines[2].split(":")[1].replace(" ", "")
                            p2p["metric"] = lines[4].split(":")[1].replace(" ", "")
                            point_to_point[p2p["neighbor_ip"]] = p2p

                area_data[router] = {"stubs": stubs, "p2p": point_to_point}
            database[area_id] = area_data
        self.ospf_database = database

    def set_static_route(self):
        """
        :metodo set_stati_route:
            :return: diccionario de datos con los siguiente informacion:
                    llave:[route + next_hop + vrf]
                    datos: global(boolean): si la ruta esta en la global (aunque si no tiene vrf tambien puede verificarse)
                           vrf(string): string de la vrf, pero si esta en la global es "null"
                           route(string): es el identificador de red
                           mask(string): es la mascara de red
                           next_hop(string): es el siguiente salto en el string
                           ad(string): distancia administrativa, si no esta explicita es "1"
                           linea(string): es la linea completa de configuracion

            :pseudocodigo:
                se utiliza el metodo set_config para obtener la configuracion del equipo
                se parsea las lineas de configuracion para obtener el disccionario de datos de las turas estaticas
                se asigna la propiedad self.static_routes
                se regresa self.static_routes.
        """
        self.set_config()

        lines_config = self.config.split("\n")

        for index, lines in enumerate(lines_config):
            ad = "1"  # distancia adminsitrativa
            if lines.startswith("ip route "):
                lines = lines.replace("\n", "")
                linea_split = lines.split(" ")
                i_route = 2;
                i_mask = 3;
                i_next_hop = 4
                i_ad = 5
                i_vrf = 3
                route_global = True;
                if (lines.startswith("ip route vrf")):
                    i_route = 4;
                    i_mask = 5;
                    i_next_hop = 6
                    i_ad = 7
                    vrf = linea_split[3]
                    route_global = False
                else:
                    vrf = "null"

                next_hop = linea_split[i_next_hop]
                pat = re.compile("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}")
                test = pat.match(next_hop)

                if test:
                    if len(linea_split) > i_ad + 1:
                        if linea_split[i_next_hop + 1].isdigit():
                            ad = linea_split[i_ad]
                else:
                    if len(linea_split) > i_next_hop + 1:
                        next_hop = linea_split[i_next_hop + 1]
                        if (len(linea_split) > i_ad + 1):
                            if (linea_split[i_ad].isdigit()):
                                ad = linea_split[i_ad + 1]
                    else:
                        next_hop = "null"
                if next_hop != "null":
                    route = linea_split[i_route]
                    mask = linea_split[i_mask]

                self.static_routes[route + next_hop + vrf] = {"global": route_global,
                                                              "vrf": vrf,
                                                              "route": route,
                                                              "mask": mask,
                                                              "next_hop": next_hop,
                                                              "ad": ad,
                                                              "linea": lines}
        return self.static_routes

    def get_recursive_routes(self,
                             ad_filter=True,
                             only_vrf=False,
                             command="show ip route",
                             recursive_pattern="default"):
        """
        :metodo get_recursive_routes:
            :parametros:
            :param ad_filter(boolean): se utiliza si es ad_filter True verifica solo las rutas con ad
                 igual a 1, si no verifica todas las rutas
                :param only_vrf(boolean): se utiliza para verificar solo vrf o todas las rutas

                :param command (string): se utiliza para definir que comando utilizara  para buscar la ruta
                generalemente y por default es "show ip route"

                :param recursive_pattern: este se utilia para determinar si la ruta es recursiva, por default
                es "default"
            :return output(strin): retorna las rutas para borrar dentro del PE

            :pseudo codigo:
                llama metodo self.set_static_routes

                se itera entre el dicccionario de rutas

                se filtra:
                    si se tiene filtro de distancia administrativa
                    si se tiene filtro de vrf
                    se envia un show ip route al equipo
                    se busca si el output de la ruta tiene un pattron de recursividad
                    si es recursiva
                        se agrega al string ouput el valor del diccionario con la llave "linea"
                        con un "no" antes
                    no es recursiva
                        no hace nada
                    se envia el output al equipo
        """
        self.set_static_route()
        # print(self.static_routes)
        output = ""
        connection = self.connect()

        for key, route in self.static_routes.items():

            if ad_filter:
                if route["ad"] == "1":
                    if (only_vrf and route["global"] == False):
                        show_route = self.send_command(connection,
                                                       "\n" + command + (" vrf ") + route["vrf"] + " " + route[
                                                           "next_hop"] + " \n", timeout=2)
                    else:
                        show_route = self.send_command(connection,
                                                       "\n" + command + (" vrf " + route["vrf"] if route[
                                                                                                       "global"] == False else " ") + " " +
                                                       route[
                                                           "next_hop"] + " \n", timeout=4)

                    if show_route.find(recursive_pattern) != -1 or show_route.find("ospf") != -1:
                        output += "no " + route["linea"] + "\n"
            else:
                if only_vrf and not route["global"]:
                    show_route = self.send_command(connection,
                                                   "\n" + command + " vrf " + route["vrf"] + " "
                                                   + route["next_hop"] + " \n", timeout=4)
                else:
                    show_route = self.send_command(connection,
                                                   "\n" + command + (
                                                       " vrf " + route["vrf"] if not route["global"] else " ") + " " +
                                                   route["next_hop"] + " \n", timeout=4)

                if show_route.find("ospf") != -1:
                    output += "no " + route["linea"] + "\n"
            self.master.log(10, output, self)
        self.close(connection)
        return output

    def get_show_ip_route(self, conection, command="show ip route", vrf=False, vrf_name="null"):
        output = ""

        return output

    def print_prefixes(self):
        pass

    def get_policy_map_interfaces(self):
        pass

    def set_ospf_topology(self, dict_ospf_neigbors={}, new_working_devices=[]):
        self.get_ip_ospf_processes()

        if (self.ip in self.self_ospf_process_list):
            as_ospf = self.self_ospf_process_list[self.ip]["ospf_process_id"]
            self.set_ip_ospf_interfaces(as_ospf=as_ospf)
            dict_ospf_neigbors[self.ip] = self

            for interface, ospf_data in self.ospf_interfaces.items():
                if (ospf_data["ospf_state"] != "down" and
                        ospf_data["ospf_neighbor"] not in dict_ospf_neigbors and
                        ospf_data["ospf_neighbor"] != "0.0.0.0"):
                    new_working_devices.append(
                        CiscoIOS(ospf_data["ospf_neighbor"], display_name=ospf_data["ospf_neighbor"],
                                 master=self.master))

        print("after rid" + self.ip + " working devices " + str(len(new_working_devices)))

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
        # todo change to parse of textfsm
        command = "show ip ospf "
        process_list = {}
        connection = self.connect()
        output = self.send_command(connection=connection, command=command)
        split_process = output.split(" Routing Process \"ospf ")
        for process in split_process[1:]:
            process_id = process.split("\n")[0].split("\"")[0]
            ospf_id = process.split("\n")[0].split(" ID ")[1]
            vrf = "global"
            if process.find("VRF") != -1:
                vrf = process.split("VRF ")[1].split("\n")[0]

            process_list[ospf_id] = {"ospf_process_id": process_id, "vrf": vrf, "ospf_id": ospf_id}
            self.master.log(10, "proceso " + process_id + " vrf " + vrf, self)

        self.self_ospf_process_list = process_list

        return self.self_ospf_process_list

    def set_ip_ospf_interfaces(self, as_ospf="14754"):
        # todo text fsm
        '''
        :param as_ospf (string):  este es un parametro para definir el sistema autionomo o el numero de proceso
         que se tendra en el output, se trabaja con ese como el global.
        :return:
        regresa un diccionario de datos con la siguiente estructura
        llave general "ip_del_vecino"
            Diccionario interno:
               ospf_ip_address(string) default(0.0.0.0): ip que utiliza paraformar la adjacencia
               ospf_state(string) default(0): se inicia con int pero es string up down etc
               ospf_protocol(string)default(0): se inicia con int pero es string
               ospf_net_type(string)default("null): se refiere al tipo de red utilizada por ospf
               ospf_neighbor_state(string)default("DOWN"): estado del vecino, se inicia en DOWN
               ospf_hello_t(string)default("0"):timer de hello ospf se incia en 0
               ospf_dead_t(string)default("0"): timer de dead ospf se inicia en 0
               ospf_neighbor(string)default("0.0.0.0"): ip del vecino se incia en 0.0.0.0
               ospf_area(string)default("x"): area del vecino se inicia en X
        a su vez se setea self.ospf_interfaces
        '''

        connection = self.connect()
        ospf_interface_output = self.send_command(connection,
                                                  "show ip ospf " + as_ospf + " interface",
                                                  self.hostname, timeout=5)
        ospf_neighbor_output = self.send_command(connection,
                                                 "show ip ospf " + as_ospf + " neighbor",
                                                 self.hostname, timeout=5)
        interface_ospf = ospf_interface_output.split("line ")
        interfaces_dict = {}
        last_interface = ""
        for index, interface in enumerate(interface_ospf):
            lines = interface.split("\n")
            interface_info = {"ospf_ip_address": "0.0.0.0", "ospf_state": "down", "ospf_protocol": "down",
                              "ospf_net_type": "null",
                              "ospf_cost": "0", "ospf_neighbor_state": "DOWN", "ospf_hello_t": "0", "ospf_dead_t": "0",
                              "ospf_neighbor": "0.0.0.0", "ospf_area": "x"}
            for line in lines:
                if line.startswith("  Internet Address "):
                    # address & area
                    address = line.split("/")[0].split(" ")[-1]
                    mask = line.split("/")[1].split(",")[0]
                    area = line.split("/")[-1].split(" Area ")[-1]
                    interface_info["ospf_area"] = area.replace(" ", "").split(",")[0]
                    interface_info["ospf_ip_address"] = address
                    interface_info["network_id"] = str(ipaddress.ip_network(address + '/' + mask, strict=False))
                    # print(area)
                if line.startswith("  Process ID"):
                    line_split = line.split(",")
                    net_type = line_split[2].replace(" Network Type ", "")
                    cost = int(line_split[-1].replace(" Cost: ", ""))
                    interface_info["ospf_net_type"] = net_type
                    interface_info["ospf_cost"] = cost
                if line.startswith("  Timer intervals configured, "):
                    line_split = line.split(",")
                    hello_t = int(line_split[1].replace("Hello ", ""))
                    dead_t = int(line_split[2].replace(" Dead ", ""))
                    interface_info["ospf_hello_t"] = hello_t
                    interface_info["ospf_dead_t"] = dead_t
                if line.startswith("    Adjacent with neighbor"):
                    line_split = line.split(" ")
                    neighbor = line_split[-1]
                    interface_info["ospf_neighbor"] = neighbor
                if line.startswith("ospf_protocol"):
                    line_split = line.split(" ")
                    protocol = line_split[-2]
                    interface_info["ospf_protocol"] = protocol

            if last_interface != "":
                # print(last_interface)
                interface_info["ospf_state"] = last_interface.split(" ")[-2].replace(",", "")

                interface_name = last_interface = last_interface.split(" ")[0]
                interface_name = interface_name.replace("TenGigabitEthernet", "Te").replace("GigabitEthernet",
                                                                                            "Gi").replace("TenGigE",
                                                                                                          "Te").replace(
                    "HundredGigE", "Hu")
                interface_info["interface"] = interface_name
                # print(interface_info)

                # print(last_interface)
                interfaces_dict[interface_name] = interface_info
            last_interface = lines[-1]
        # print(interfaces_dict)
        output_ospf_neighbor = ospf_neighbor_output
        neighbor_split = output_ospf_neighbor.split("\n")
        for line in neighbor_split:
            for interface, interface_info in interfaces_dict.items():
                if (line.find(interface_info["ospf_neighbor"]) > -1):
                    if (line.find("FULL") > -1):
                        interface_info["ospf_neighbor_state"] = "FULL"
        self.ospf_interfaces = interfaces_dict

        self.master.log(10, self.ospf_interfaces, self)
        connection.disconnect()
        return interfaces_dict

    def set_ip_bgp_neighbors(self, address_family="ipv4 unicast"):
        # todo change to parse of textfsm
        '''

        :param address_family(string) default("ipv4 unicast"):
        :return:
        '''
        if self.bgp_neighbors is None:
            self.bgp_neighbors = dict()

        connection = self.connect()
        command = "show bgp " + address_family + " neighbors"
        show_bgp_neighbors = self.send_command(connection, command, self.hostname, timeout=5)
        neighbor_string_split = show_bgp_neighbors.split("BGP neighbor is ")
        for neighbor_string in neighbor_string_split:
            if (neighbor_string.find('  remote AS ') > 0):
                bgp_session = {"bgp_neighbor_ip": "0.0.0.0",
                               "bgp_remote_as": 0, "bgp_session_type": 0,
                               "bgp_state": 0,
                               "bgp_time_in_state": 0,
                               "bgp_address_family": "",
                               "bgp_total_prefixes_advertised": 0,
                               "bgp_accepted_prefixes": 0,
                               "bgp_policy_out": "NA",
                               "bgp_policy_in": "NA",
                               "bgp_description": "NA",
                               "bgp_prefix_in": "NA",
                               "bgp_prefix_out": "NA"
                               }

                lines_neighbor = neighbor_string.split("\n")
                for line in lines_neighbor:
                    if (line.find("  Incoming update prefix filter list is ") > -1):
                        bgp_session["bgp_prefix_in"] = line.replace("  Incoming update prefix filter list is ", "")
                    if (line.find("  Outgoing update prefix filter list is ") > -1):
                        bgp_session["bgp_prefix_out"] = line.replace("  Outgoing update prefix filter list is ", "")
                    if (line.find(" Description: ") > -1):
                        bgp_session["bgp_description"] = line.replace(" Description: ", "")
                    if (line.find("For address family:") > -1):
                        bgp_session["bgp_address_family"] = line.replace(" For address family: ", "")
                    if (line.find("Prefixes Current:") > -1):
                        line = line.replace("Prefixes Current:", "")
                        splitline = re.sub(" +", " ", line).split(" ")
                        bgp_session["bgp_total_prefixes_advertised"] = splitline[0]
                        bgp_session["bgp_accepted_prefixes"] = splitline[1]
                    if (line.find("  Route map for outgoing advertisements is ") > -1):
                        bgp_session["bgp_policy_out"] = line.replace("  Route map for outgoing advertisements is ", "")
                    if (line.find("  Route map for incoming advertisements is ") > -1):
                        bgp_session["bgp_policy_in"] = line.replace("  Route map for incoming advertisements is ", "")

                    if (line.find("  remote AS ") > -1):
                        line_split = line.split(",")
                        bgp_session["bgp_neighbor_ip"] = line_split[0]
                        bgp_session["bgp_remote_as"] = line_split[1].replace("  remote AS ", "")
                        if (bgp_session["bgp_remote_as"].find("vrf") > 0):
                            bgp_session["bgp_remote_as"] = line_split[2].replace("  remote AS ", "")
                            bgp_session["bgp_vrf"] = line_split[1].replace("vrf", "").replace(" ", "")
                            bgp_session["bgp_session_type"] = line_split[4].replace("", "")
                        else:
                            bgp_session["session_type"] = line_split[2]
                    if (line.find("BGP state") > 0):
                        line_split = line.replace("BGP state = ", "").split(",")
                        bgp_session["bgp_state"] = line_split[0].replace(" ", "")
                        if (len(line_split) > 1):
                            bgp_session["time_in_state"] = line_split[1].replace(" up for ", "")
                    if (bgp_session["bgp_state"] != 0 and bgp_session["bgp_time_in_state"] == 0 and line.find(
                            "Last reset") > 0):
                        line_split = line.split(",")
                        bgp_session["bgp_time_in_state"] = line_split[0].replace("Last reset", "")
                # print("something")
                bgp_session["bgp_address_family"] = address_family
                self.bgp_neighbors[bgp_session["bgp_neighbor_ip"]] = bgp_session
                # print(self.bgp_neighbors[address_family][bgp_session["neighbor_ip"]])

        return self.bgp_neighbors

    def set_mpls_ldp_interfaces(self, address_family="ipv4 unicast"):
        # todo change to parse of textfsm
        connection = self.connect()
        command = "show mpls interfaces"
        show_mpls_interface = self.send_command(connection, command, self.hostname, timeout=5)
        # neighbor_string_split = show_bgp_neighbors.split("BGP neighbor is ")
        command = "show mpls ldp neighbor detail"
        show_mpls_ldp_neighbor = self.send_command(connection, command, self.hostname, timeout=5)
        mpls_interface_lines = show_mpls_interface.split("\n")
        mpls_interface_lines.pop(0)
        interfaces_mpls = {}
        for mpls_interface_line in mpls_interface_lines:
            interface = mpls_interface_line[:21].replace("TenGigabitEthernet", "Te").replace("GigabitEthernet",
                                                                                             "Gi").replace(" ",
                                                                                                           "").replace(
                "\t", "")
            configured = mpls_interface_line[22:37]
            operational = mpls_interface_line[57:60].find("Yes") > -1
            ldp = configured.find("ldp") > -1
            ip_configured = configured.find("Yes") > -1
            interfaces_mpls[interface] = {"interface": interface, "ldp_enable": ldp,
                                          "ldp_operational_mpls": operational, "ldp_ip_configured": ip_configured}
            interfaces_mpls[interface]["ldp_neighbor_ip"] = "0.0.0.0"
            interfaces_mpls[interface]["ldp_state"] = False

        strings_per_ldp_neighbor = show_mpls_ldp_neighbor.split("    Peer LDP Ident: ")
        ldp_neighbor = {}
        strings_per_ldp_neighbor.pop(0)
        for string_ldp_neighbor in strings_per_ldp_neighbor:
            password = string_ldp_neighbor.find("MD5") > -1
            lines_ldp_neighbor = string_ldp_neighbor.split("\n")
            interfaces = {}
            neighbor_ip = "0.0.0.0"
            state = False
            for line_ldp_neighbor in lines_ldp_neighbor:

                if line_ldp_neighbor.find("Local LDP") > -1:
                    neighbor_ip = line_ldp_neighbor.split(";")[0].replace(":0", "").replace(" ", "")

                if line_ldp_neighbor.find("	State: ") > -1:
                    state = line_ldp_neighbor.find("Oper") > -1
                if line_ldp_neighbor.find("Up time: ") > -1:
                    uptime = line_ldp_neighbor.split(";")[0].replace("	Up time: ", "")
                if line_ldp_neighbor.find(" Src IP ") > -1:
                    interface = line_ldp_neighbor.split(";")[0].replace(" ", "").replace("TenGigabitEthernet",
                                                                                         "Te").replace(
                        "GigabitEthernet", "Gi").replace("\t", "")
                    ip_interface_neighbor = line_ldp_neighbor.split(":")[1].replace(" ", "")
                    interfaces[interface] = {"interface": interface, "ldp_ip": ip_interface_neighbor}
                    interfaces_mpls[interface]["ldp_neighbor_ip"] = neighbor_ip
                    interfaces_mpls[interface]["ldp_state"] = state
                    interfaces_mpls[interface]["interface"] = interface

            ldp_neighbor[neighbor_ip] = {"ip": neighbor_ip, "state": state, "password": password,
                                         "interfaces": interfaces, "uptime": uptime}
        self.ldp_neighbors = ldp_neighbor
        self.mpls_ldp_interfaces = interfaces_mpls

        return ldp_neighbor, interfaces_mpls

    def get_platform(self):
        self.set_snmp_community()
        self.set_snmp_plattform()
        return self.platform

    def set_pim_interfaces(self):
        # todo parse textfsm.. not user for the moment
        connection = self.connect()
        command = "show "
        command2 = 'show ip pim neighbor | b Add'
        show_pim_neighbor = self.send_command(connection, command2, self.hostname, timeout=5)
        command3 = 'show ip pim interface  | b Prior'
        show_pim_interface = self.send_command(connection, command3, self.hostname, timeout=5)
        show_pim_neighbor = re.sub(' +', " ", show_pim_neighbor)
        show_pim_interface = re.sub(' +', " ", show_pim_interface)

        interfaces = {}
        for pim_enable_interface in show_pim_interface.split("\n")[1:]:
            pim_enable_interface = pim_enable_interface.split(" ")

            interface = pim_enable_interface[1].replace("TenGigabitEthernet", "Te").replace("HundredGigE",
                                                                                            "Hu").replace(
                "GigabitEthernet", "Gi")
            interfaces[interface] = {"interface": interface}

            interfaces[interface]["pim_neighbor"] = "0.0.0.0"
            interfaces[interface]["pim_neighbor_count"] = pim_enable_interface[3]
            interfaces[interface]["pim_hello_timer"] = pim_enable_interface[4]
            interfaces[interface]["pim_dr_priority"] = pim_enable_interface[5]
            interfaces[interface]["pim_dr"] = pim_enable_interface[6]
            interfaces[interface]["pim_state"] = interfaces[interface]["pim_dr"] != "0.0.0.0"
        pim_neighbors = {}
        for pim_neighbor in show_pim_neighbor.split("\n")[1:]:
            pim_neighbor = pim_neighbor.split(" ")
            ip_neighbor = pim_neighbor[0]
            interface = pim_neighbor[1].replace("TenGigabitEthernet", "Te").replace("HundredGigE", "Hu").replace(
                "GigabitEthernet", "Gi")
            uptime = pim_neighbor[2]

            pim_neighbors[ip_neighbor] = {"ip_neighbor": ip_neighbor, "interface": interface, "uptime": uptime}

            interfaces[interface]["pim_state"] = True if ip_neighbor != "0.0.0.0" else False
            interfaces[interface]["pim_neighbor"] = ip_neighbor
        # print("finish IOS")
        self.pim_interfaces = interfaces
        self.pim_neighbors = pim_neighbors

        return interfaces, pim_neighbors

    def get_interfaces_stats(self, interfaces_index=[]):
        output = "";
        for index in interfaces_index:
            if index in self.interfaces:
                output.join(self.interfaces[index].get_interface_summary())
        return output

    def set_log(self, filter=""):
        # todo parse log per hour and class log_line to check time
        connection = self.connect()
        command = "show logging " + ("" if filter == "" else " | i " + filter)

        self.log = reversed(self.send_command(connection=connection, command=command, timeout=10).split("\n"))
        return self.log

    def get_log(self, filter=""):
        return self.log

    def ospf_database_router(self, process_id='1'):
        return self.send_command_and_parse(command="show ip ospf " + process_id + " database router",
                                           template_name="show ip ospf database router.template")

    def ospf_area_adjacency_p2p(self, process_id='1', area='0'):
        ospf_database = self.ospf_database_router(process_id=process_id)

        p2p = [{'router_id': row['router_id'],
                'neighbor_ip': row['link_id'],
                'interface_ip': row['link_data'],
                'area': row['area'],
                'metric': row['metric'],
                'network': str(ipaddress.IPv4Network(row['link_data'] + "/30", strict=False).network_address)

                }
               for row in ospf_database if row['area'] == area and row['lsa_type'] == 'point-to-point']
        routers = {row['router_id'] for row in ospf_database}
        p2p_reduced = dict()
        for link in p2p:
            if link['network'] not in p2p_reduced:
                p2p_reduced[link['network']] = [link]
            else:
                p2p_reduced[link['network']].append(link)
        self.verbose.debug("{0}, {1}".format(p2p_reduced, routers))
        return p2p_reduced, routers

    def print_bgp_neighbors(self, address_family="ipv4 unicast"):
        # todo crear un output en excel
        if hasattr(self, "bgp_neighbors"):
            if not address_family in self.bgp_neighbors:
                self.set_ip_bgp_neighbors(address_family)
        else:
            self.set_ip_bgp_neighbors(address_family)

        columns = []
        output = ""
        for key, neighbor in self.bgp_neighbors.items():
            output = output + key + "!"
            if len(columns) == 0:
                columns = neighbor.keys()
            for name_column, data_column in neighbor.items():
                output = output + str(data_column) + "!"
            output = output + "\n"
        header = "bgp_ip_neighbor!"
        for column in columns:
            header = header + column + "!"
        output = header + "\n" + output

        return output

    def set_interfaces(self, template_name="show_interfaces_detail_ios.template"):

        interfaces = self.send_command_and_parse(command="show interfaces"
                                                 , template_name=template_name, timeout=15)
        for interface in interfaces:
            interface["if_index"] = normalize_interface_name(interface["if_index"])
            interface_object = InterfaceUfinet(self, interface)
            self.interfaces[interface["if_index"]] = interface_object
            self.interfaces_ip[str(interface_object.ip)] = interface_object

        return self.interfaces

    def set_snmp_community(self):

        for community in self.master.communities:
            self.community = community
            self.set_snmp_hostname()
            if self.hostname != "no_snmp":
                self.logger_connection.info("{0} snmp community set".format(self.ip))
                break
        else:
            self.logger_connection.info("{0} unable to set snmp community".format(self.ip))

    def set_snmp_hostname(self):
        oid = "1.3.6.1.2.1.1.5.0"
        cmd_gen = cmdgen.CommandGenerator()
        error_indication, error_status, error_index, var_binds = cmd_gen.getCmd(cmdgen.CommunityData(self.community),
                                                                                cmdgen.UdpTransportTarget(
                                                                                    (self.ip, 161)),
                                                                                oid
                                                                                )
        hostname = "no_snmp"
        for name, val in var_binds:
            hostname = str(val).split(".")[0]
        self.hostname = hostname

    def set_snmp_plattform(self):

        platfforms = {"9K": "CiscoXR", "ASR920": "CiscoIOS", "900": "CiscoIOS", "default": 'CiscoIOS'}
        oid = ".1.3.6.1.2.1.1.1.0"
        a_device = (self.ip, self.community, 161)
        snmp_data = snmp_get_oid(a_device=a_device, oid=oid, display_errors=False)
        try:
            snmp_text = snmp_extract(snmp_data)
        except:
            snmp_text = "default"
        for pattern, platform_name in platfforms.items():
            if pattern in snmp_text:
                self.platform = platform_name
                break

    def set_snmp_location_attr(self):

        self.set_snmp_location()

        data = self.parse_txtfsm_template(template_name="snmp_location_attr_profile.template", text=self.snmp_location)
        if data:
            for attr, value in data[0].items():
                try:
                    value = value if value != "" else "0"
                    setattr(self, attr, value)
                    self.dev.info("snmp location atrubute ccheck " + self.ip + " " + attr + getattr(self, attr))
                except AttributeError as e:
                    self.dev.warning("set_snmp_location_attr ip" + self.ip + " err " + repr(e))

    def set_snmp_location(self):
        if (self.community == ""):
            self.set_snmp_community()
        oid = ".1.3.6.1.2.1.1.6.0"
        self.snmp_location = ""
        try:
            a_device = (self.ip, self.community, 161)
            snmp_data = snmp_get_oid(a_device=a_device, oid=oid, display_errors=True)
            snmp_text = snmp_extract(snmp_data)
            self.snmp_location = snmp_text
        except Exception as e:
            self.logger_connection.error("unable to get snmp location {0} {1}".format(self.ip, repr(e)))

    def set_yed_xy(self):
        self.set_snmp_location()
        try:
            self.x = str(int(self.snmp_location.split(",")[0].split(":")[1]))
            self.y = str(int(self.snmp_location.split(",")[1].split(":")[1]))
        except:
            self.x = "0"
            self.y = "0"
            print(self.ip, self.snmp_location, " unable to split location ")

    def get_physical_interfaces(self):
        if self.interfaces is None:
            self.set_interfaces()
        return {key: interface for key, interface in self.interfaces.items()
                if "." not in interface["description"]}

    def set_inventory(self):

        replace_in_name = ["module", " mau ", "/CPU0", "TenGigE", 'GigE', "/SP"]
        command = "admin show inventory"
        template = "show inventory.template"
        inventory = self.send_command_and_parse(template_name=template,
                                                command=command)
        parts = [{'description': part['description'],
                  'name': replace(part['name'], replace_in_name),
                  'pid': "FAN",
                  'sn': 'N/A',
                  'vid': part['vid']}
                 for part in inventory if "Generic Fan" in part["description"] and part["pid"] == ''] \
                + \
                [{'description': part['description'],
                  'name': replace(part['name'], replace_in_name),
                  'pid': part['pid'],
                  'sn': part['sn'],
                  'vid': part['vid']} for part in inventory if "Generic Fan" not in part["description"]]

        self.inventory = parts
        return parts

    def set_chassis(self, from_db=False):
        print("set _chassis")
        if from_db:
            print("set _chassis db")
            self.verbose.warning("set_chassis:DB")
            CiscoPart.chassis_from_db(self)
        else:
            CiscoPart.create_inventory_tree(self, self.set_inventory())
        return self.chassis

    def draw_device_hardware(self, x, y):
        self.set_chassis()
        master = Tk()

        canvas = Canvas(master, width=300, height=1000)
        self.chassis.draw_in_canvas(canvas, x, y, recursive=True)
        canvas.pack()
        mainloop()

    def get_interfaces_dict_data(self):
        self.set_interfaces()
        interface_data_list = []
        for interface_index, interface in self.interfaces.items():
            interface_dict = interface.dict_data()
            interface_dict["device"] = self.hostname
            interface_dict["ip_device"] = self.ip
            interface_data_list.append(interface_dict)
        return interface_data_list

    def set_interfaces_transciever_optics(self):
        parser = self.load_template("transciever_ios")
        command = "show interfaces trans "
        connection = self.connect()
        output = connection.send_command(command)
        trasnciever_data = parser.ParseText(output)

    def get_yed_node(self):

        shape = 'rectangle3d'
        shape_fill = '#442233'
        height = 275
        width = 275
        if "9K" in self.hostname:
            shape = 'hexagon'
            height = 350
            width = 350
        if "NAP" in self.hostname:
            shape_fill = '#90d680'
        additional_label = [{"text": self.ip, "modelPosition": "s"},
                            {"text": self.hostname, "modelPosition": "n"}]
        node = pyyed.Node(node_name=self.ip,
                          additional_labels=additional_label,
                          font_size='23',
                          shape_fill=shape_fill,
                          edge_color="#442233",
                          height=str(height), width=str(width), edge_width='8',
                          shape=shape, y=self.y, x=self.x
                          )
        return node

    def get_vs(self):
        try:
            image = '../static/img/' + self.platform + CiscoIOS.images[self.country] + '.png'
        except Exception as e:
            image = '../static/img/' + self.platform + '.png'
            self.verbose.warning("get_vs:" + self.ip + " err " + str(e))

        if self.uid_db() == 0:
            self.save()
        return {'mass': 10, 'id': self.uid, 'label': self.ip + " " + self.hostname, 'font': {'size': '8'},
                'image': image, 'shape': 'image'}

    def get_vfis_interface_per_service_instance(self):
        '''
        set service _instance
        Value id (\d+)
        Value description (.*)
        Value interface (\S+)
        Value vlan (\S+)
        Value state (\S+)

        set pseudowire [Value vc_id (\d+)
                        Value vc_status (\S+)
                        Value destination_ip ((\d{1,3}\.){3}\d{1,3})
                        Value interface (\S+)
                        Value interface_state (\S+)
                        Value vfi (VFI)
                        Value output_interface (\S+)
                        Value preferred_path (\S+(\s\S+)?)
                        Value preferred_path_state (\S+(\s\S+)?)
                        Value default_path (\w+)
                        Value next_hop (\S+)
                        Value local_mtu (\d+)
                        Value remote_mtu (\d+)
                        Value ldp_state (\w+)
                        Vlan
            ]
        set briddomain
        :return:
        '''

        self.set_pseudowires()
        self.set_service_instances()
        self.set_bridge_domains()
        temporal_service_instance = dict(self.service_instances)

        for index, si in temporal_service_instance.items():
            index_interface = normalize_interface_name(si["interface"])
            bd = self.bridge_domain_per_interface_si(interface=index_interface, si=si["id"])
            if bd is not None:
                si["pws_neighbor"] = ""
                si["pws_vcid"] = ""
                si["vfi"] = bd.get_string_vfi()
            pws = self.pseudowire_per_interface_vlan(interface=index_interface, vlan=si["vlan"])

            if len(pws) > 0:
                if "vfi" not in si:
                    si["vfi"] = ""
                si["pws_neighbor"] = pws[0]["destination_ip"]
                si["pws_vcid"] = pws[0]["vc_id"]
        pprint(temporal_service_instance)
        return temporal_service_instance

    def pseudowire_per_interface_vlan(self, interface, vlan):
        return [pw for key, pw in self.pseudowires.items() if
                normalize_interface_name(pw["interface"]) == interface and pw["vlan"] == vlan]

    def bridge_domain_per_interface_si(self, interface, si):
        for bd in self.bridge_domains.values():
            if bd.interface_bridge_domain(interface, si):
                return bd
        return None

    def service_instance_per_vlan(self, interface, vlan_id):
        interface = normalize_interface_name(interface)
        for id_si, si in self.service_instances.items():
            if normalize_interface_name(si["interface"]) == interface and vlan_id == si["vlan"]:
                return id_si, si

    def configure_snmp_location(self, text):
        command = "configure terminal \n\n \n \n \n  snmp-server location " + text + "\n\nexit\nwr\n"
        connection = self.connect()
        self.verbose.warning("command " + self.ip + " + " + command)
        self.verbose.warning("response:" + self.ip + " + " + self.send_command(connection=connection, command=command))

    def get_xy_direction(self, x, y):
        direction = "E"
        try:
            if int(self.x) < int(x) - 150:
                direction += "E"
            elif int(self.x) > int(x) + 150:
                direction += "W"
            if int(self.y) < int(y) - 150:
                direction = "N"
            elif int(self.y) > int(y) + 150:
                direction += "S"
        except Exception as e:
            pass
        return direction

    def get_next_edge_point(self, x, y, last=True):
        index = -1 if last else 0
        direction = self.get_xy_direction(x, y)
        for letter in direction:
            if (letter in self.yed_edges_points):
                if (len(self.yed_edges_points[letter]) > 0):
                    return self.yed_edges_points[letter].pop(index)
        return ("0", "0")

    def uid_db(self):
        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                sql = '''SELECT uid FROM network_devices WHERE ip=%s'''
                cursor.execute(sql, (self.ip,))
                result = cursor.fetchone()
                if (result):
                    self.uid = result['uid']
                    connection.close()
                    return self.uid
                else:
                    self.uid = 0
                    connection.close()
                    return 0
        except Exception as e:
            self.log_db.warning(self.ip + " " + str(e))

            return 0

    def in_db(self):
        if self.uid != 0:
            return True
        elif self.uid_db() == 0:
            return False
        else:
            return True

    def get_uid_save(self):
        if not self.in_db():
            self.save(
            )
        return self.uid

    def save(self):

        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                sql = '''INSERT INTO network_devices(ip,hostname,platform)
                VALUES (%s,%s,%s)'''
                cursor.execute(sql, (self.ip, self.hostname, self.platform))
                connection.commit()
                self.uid = cursor.lastrowid
                self.db_log(":SAVED uid:" + self.uid)
            return self.uid
        except Exception as e:
            print(e)
            return False

    def get_interfaces_filtered(self, filters):

        interfaces = self.interfaces.values()
        for attribute, filter in filters.items():
            interfaces = [interface for interface in interfaces
                          if filter in getattr(interface, attribute)]
            print(self.ip, attribute, filter, interfaces)
        return interfaces

    def ip_explicit_paths(self, template_name="ip explicit-path ios.template"):
        list_of_hops = self.send_command_and_parse(command="show run | s ip explicit-path", template_name=template_name)
        path_names = {hop['name'] for hop in list_of_hops}
        self.explicit_paths = {}
        for path_name in path_names:
            self.explicit_paths[path_name] = IpExplicitPath(name=path_name, hops=[hop for hop in list_of_hops if
                                                                                  hop["name"] == path_name],
                                                            parent_device=self)

        return self.ip_explicit_paths

    def add_hop_ip_explicit_paths(self, hop, ip_reference_hop, index_way="before"):
        self.ip_explicit_paths()
        new_paths = []

        for path in [path_ for key, path_ in self.explicit_paths.items() if path_.ip_on_path(ip=ip_reference_hop)]:
            new_paths.append(path.copy_path_new_hop(ip_reference_hop=ip_reference_hop, hop=hop, index_way=index_way))

        return new_paths
