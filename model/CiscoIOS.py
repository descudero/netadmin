import ipaddress
from model.CiscoPart import CiscoPart
import re
import sqlite3 as sql
import shelve
import psycopg2 as pmsql
from netmiko import ConnectHandler
from netmiko import NetMikoAuthenticationException
from netmiko import NetMikoTimeoutException
from paramiko import SSHException
from paramiko import AuthenticationException
import os
from model.BaseDevice import BaseDevice as Parent
from model.InterfaceIOS import InterfaceIOS
from multiping import multi_ping
from pprint import pprint
from pysnmp.entity.rfc3413.oneliner import cmdgen
from tkinter import *


class CiscoIOS(Parent):

    def send_command(self, connection, command, pattern="#", read=True, timeout=4):
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

        self.master.log(20, "sent " + self.ip + " command " + command, self)
        output = ""
        retry_counter = 0
        while output == "" and retry_counter < 3:
            retry_counter += 1
            try:
                if hasattr(self, "hostname"):
                    # print("hostname"+self.hostname)
                    pattern = self.hostname
                    # print(command   )
                    output = connection.send_command(command_string=command,
                                                     expect_string=pattern, delay_factor=timeout, max_loops=100)
                else:
                    output = connection.send_command(command_string=command,
                                                     delay_factor=timeout,
                                                     expect_string=pattern,
                                                     max_loops=50)
            except (OSError) as e:
                output = ""
        self.master.log(2, " RX " + self.ip + " output " + output, self)
        return output

    def internet_validation_arp(self, test_name, vrf):
        test_ping = shelve.open(test_name + self.display_name)
        if ("responses" in test_ping):
            test_ping["responses"]
            responses, no_responses = multi_ping(test_ping["responses"].keys(), timeout=3, retry=2,
                                                 ignore_lookup_errors=True)
            no_responses2 = no_responses
            test_ping["test_no_responses"] = no_responses

            for i in range(0, 5):
                if (len(no_responses2) > 0):
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
        return self.service_instances[interface + ":" + service_instance]

    def set_pseudo_wire_class(self):
        print("set set_pseudo_wire_class ip self" + self.ip)
        self.pseudo_wire_class = {}
        command = "show run | s pseudowire-class"
        connection = self.connect()
        output = self.send_command(command=command, connection=connection)
        connection.disconnect()
        for pw_class in output.split("pseudowire-class ")[1:]:
            # print(pw_class)
            lines = pw_class.split("\n")
            data = {}
            data["encapsulation"] = lines[1].replace(" encapsulation ", "")

            if (len(lines) > 2):
                if (lines[2].find("Tunnel")):
                    data["interface"] = lines[2].replace(" preferred-path interface ", "").replace(" ", "").replace(
                        "disable-fallback", "")
            self.pseudo_wire_class[lines[0]] = data

    def set_mpls_te_tunnels(self):
        print("set set_mpls tunnles self" + self.ip)
        self.mpls_te_tunnels = {}
        command = "show mpls traffic-eng tunnels detail"
        connection = self.connect()
        output = self.send_command(command=command, connection=connection)
        connection.disconnect()
        for lsp in output.split("LSP Tunnel ")[1:]:
            lsp_data = {}
            lsp_data["name"] = lsp.split(" is ")[0].replace(" ", "")
            lsp_data["state"] = lsp.split("connection is")[1].replace(" ", "").split("\n")[0]
            for line in lsp.split("\n"):
                if (line.find("InLabel  : ") > -1):
                    data = line.replace("InLabel  : ", "").split(",")
                    lsp_data["interface_in"] = CiscoIOS.get_normalize_interface_name(data[0].replace(" ", ""))
                    lsp_data["label_in"] = data[1]
                if (line.find("OutLabel :") > -1):
                    data = line.replace("OutLabel :", "").split(",")
                    if (len(data) > 1):
                        lsp_data["interface_out"] = CiscoIOS.get_normalize_interface_name(data[0].replace(" ", ""))
                        lsp_data["label_out"] = data[1].replace(" ", "")
                if (line.find("Src") > -1 and line.find("Dst")):
                    data = line.split(",")
                    lsp_data["source_ip"] = data[0].replace("Src", "").replace(" ", "")
                    lsp_data["destination_ip"] = data[1].replace("Dst", "").replace(" ", "")
                    lsp_data["tunnel_id"] = data[2].replace(" Tun_Id ", "").replace(" ", "")
                    lsp_data["tunnel_instance"] = data[3].replace("Tun_Instance ", "").replace(" ", "")
            if ("tunnel_instance" not in lsp_data):
                # print("not tunnel instance")
                # print(lsp_data)
                pass
            else:
                self.mpls_te_tunnels[lsp_data["tunnel_instance"]] = lsp_data
        # pprint(self.mpls_te_tunnels)

    def set_service_instances(self):
        print("set set service intances ip self" + self.ip)
        self.service_instances = {}
        command = "show ethernet service instance detail"
        connection = self.connect()
        output = self.send_command(command=command, connection=connection)
        connection.disconnect()
        # print(output)
        for service_instance in output.split("Service Instance ID: ")[1:]:
            lines = service_instance.split("\n")

            service_data = {}
            id = lines[0].replace(" ", "")
            service_data["id"] = id
            for line in lines:
                if (line.find("Service Instance Type: ") > -1):
                    service_data["type"] = line.split(" ")[3]
                if (line.find("Encapsulation: ") > -1):
                    # print(line)

                    if (line.find("untagged") > -1 or line.find("default") > -1):
                        service_data["dot1q"] = "untagged"
                    else:
                        try:
                            service_data["dot1q"] = line.split(" ")[2]
                        except:
                            print("no funciono el dot1q " + line)
                            service_data["dot1q"] = "na"
                if (line.find("Associated Interface: ") > -1):
                    service_data["interface"] = CiscoIOS.get_normalize_interface_name(line.split(" ")[2])
                if (line.find("Description: ") > -1):
                    service_data["description"] = line.replace("Description:", "").split(" ")[1]
            if ("description" not in service_data):
                service_data["description"] = "null"
            if ("service_instace" not in service_data):
                service_data["service_instance"] = service_data["id"]
            try:
                self.service_instances[service_data["interface"] + ":" + service_data["id"]] = service_data

            except:
                print("not interface data " + self.ip)
                print(service_instance)
                pprint(service_data)
        # pprint(self.service_instances)

    def get_template_by_tunnel_id(self, tunnel_id):
        pprint("tunerl id for vfi " + tunnel_id)
        for name, template in self.template_type_pseudowires.items():

            if (template["interface"] == "Tunnel" + str(tunnel_id)):
                return name
        return "null"

    def get_vfi_by_template(self, template_name):
        pprint("vfi for template " + template_name)
        for name, vfi in self.vfis.items():
            for pseudowire in vfi["pseudowires"]:
                print(pseudowire)
                if (pseudowire["template"] == template_name):
                    print("get vfi " + name)
                    return name
        return "null"

    def get_interfaces_instance_by_vfi(self, vfi):
        pprint(self.ip + " interfaces by vfi " + vfi)
        for name, bridge in self.bridge_domains.items():
            if "vfi" in bridge:
                if (bridge["vfi"] == vfi):
                    pprint(self.ip + " interfaces by vfi " + vfi)
                    pprint(bridge["interfaces"])
                    return bridge["interfaces"]
        return []

    def get_service_instance_by_interfaces(self, interfaces):
        pprint(self.ip + " instances by interfaces ")
        pprint(interfaces)
        service_intances = []
        if (interfaces):
            for interface in interfaces:
                try:
                    service_intances.append(
                        self.get_service_instance_data(interface["interface"], interface["service_instance"]))

                except:
                    pass
            # pprint(service_intances)
            return service_intances
        return []

    def get_service_instance_by_tunnel_id_vfi(self, tunnel_id):
        template = self.get_template_by_tunnel_id(tunnel_id=tunnel_id)
        vfi = self.get_vfi_by_template(template_name=template)
        interfaces = self.get_interfaces_instance_by_vfi(vfi=vfi)

        service_instances = self.get_service_instance_by_interfaces(interfaces)
        return service_instances

    def set_template_type_pseudowires(self, ):
        self.template_type_pseudowires = {}
        command = "show run | s template type"
        connection = self.connect()
        output = self.send_command(command=command, connection=connection)
        connection.disconnect()
        for template in output.split("template type pseudowire")[1:]:
            data = {}
            lines = template.split("\n")
            data["name"] = lines[0].replace(" ", "")

            if (len(lines) > 2):
                data["interface"] = lines[2].replace(" preferred-path interface", "").replace(" ", "")
            else:
                data["interface"] = "null"
            self.template_type_pseudowires[data["name"]] = data

    def set_bridge_domains(self):
        self.bridge_domains = {}
        command = "show run | s bridge-domain "
        connection = self.connect()
        output = self.send_command(command=command, connection=connection)
        connection.disconnect()
        for bridge in output.split("bridge-domain ")[1:]:
            data = {}
            data["interfaces"] = []
            lines = bridge.split("\n")
            data["name"] = lines[0].replace(" ", "")
            for line in lines[1:]:
                if (line.find("service-instance") > -1):
                    split = line.split(" ")

                    data["interfaces"].append(
                        {"interface": CiscoIOS.get_normalize_interface_name(split[2]), "service_instance": split[4]})
                if (line.find("vfi") > -1):
                    data["vfi"] = line.replace(" member vfi ", "")
            self.bridge_domains[data["name"]] = data
        # pprint(self.bridge_domains)

    def set_vfis(self):
        self.vfis = {}
        command = "show run | s l2vpn vfi "
        connection = self.connect()
        output = self.send_command(command=command, connection=connection)
        connection.disconnect()
        for bridge in output.split("l2vpn vfi context ")[1:]:
            data = {}
            data["pseudowires"] = []
            lines = bridge.split("\n")
            data["name"] = lines[0].replace(" ", "")
            for line in lines[1:]:
                if (line.find("member ") > -1):
                    split = line.split(" ")
                    pseudowire = {}
                    pseudowire["destination"] = split[1]
                    pseudowire["id"] = split[3]
                    if (line.find("template") > -1):

                        try:
                            pseudowire["template"] = split[5]
                        except:
                            try:
                                pseudowire["template"] = split[4]


                            except:
                                pseudowire["template"] = "mpls"
                                print("error line " + line)
                                print(split)


                    else:
                        pseudowire["template"] = "mpls"
                    data["pseudowires"].append(pseudowire)
            self.vfis[data["name"]] = data

    def set_pseudowires(self):
        print("set pseudowires ip self" + self.ip)
        self.pseudowires = {}
        command = "show run | i xconnect"
        connection = self.connect()
        output = self.send_command(command=command, connection=connection)
        command = "show xconnect all | i ac"
        connection = self.connect()
        output2 = self.send_command(command=command, connection=connection)
        connection.disconnect()
        for xconnect in output.split("\n"):
            data_xconnect = {}
            xconnect = xconnect.replace("  xconnect ", "")
            if (xconnect.find("encapsulation mpls") > -1):
                data = xconnect.split(" ")
                # print(data)
                data_xconnect["destination"] = data[0]
                data_xconnect["id"] = data[1].replace(" ", "")
                if (len(data) > 4):
                    data_xconnect["pw_class"] = data[5]
                else:
                    data_xconnect["pw_class"] = "null"
                self.pseudowires[data_xconnect["id"]] = data_xconnect
        # pprint(self.pseudowires)
        for xconnect in output2.split("\n")[1:]:
            xconnectsplit = re.sub(" +", " ", xconnect).split(" ")
            # print(xconnectsplit)
            try:
                id = xconnectsplit[7].split(":")[1]

            except:
                try:
                    id = xconnectsplit[6].split(":")[1]
                except:
                    id = "null"

            try:
                interface = xconnectsplit[3].split(":")[0]
                service_instance = xconnectsplit[3].split(":")[1].split("(")[0]
            except:
                interface = "null"
                service_instance = "0"
            try:
                self.pseudowires[id]["interface"] = interface
                self.pseudowires[id]["service_instance"] = service_instance
            except:
                print("unable to set interface" + id + " device " + self.ip)

        # print(self.pseudowires)

    def get_pw_class_by_tunnel_id(self, tunnel_id):
        print(tunnel_id + " router " + self.ip)
        for name, pw_class in self.pseudo_wire_class.items():
            if (pw_class["interface"] == "Tunnel" + str(tunnel_id)):
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

    def set_conected_routes(self, vrf="default"):

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
            interface = CiscoIOS.get_normalize_interface_name(
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
        device_type = "cisco_ios_"
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
        connection = "null"

        retry_counter = 0

        if (not hasattr(self, "jump_gateway")):
            while type(connection) is str and retry_counter != 3:
                retry_counter += 1
                self.master.log(20, "conection ip " + self.ip + " # " + str(retry_counter), self)
                try:
                    connection = ConnectHandler(device_type=device_type + "ssh"
                                                , ip=self.ip,
                                                username=self.master.username,
                                                password=self.master.password)
                    self.master.log(20, "telnet up " + self.display_name, self)

                except (
                        AuthenticationException, NetMikoTimeoutException, EOFError, SSHException,
                        ConnectionAbortedError,
                        ValueError, ConnectionRefusedError) as e:
                    try:

                        connection = ConnectHandler(device_type=device_type + "telnet",
                                                    ip=self.ip, username=self.master.username,
                                                    password=self.master.password)
                        self.master.log(20, "ssh up " + self.display_name, self)

                    # try ssh

                    except (NetMikoAuthenticationException, SSHException, EOFError, ConnectionAbortedError, ValueError,
                            ConnectionRefusedError) as e:
                        print(self.ip + " not able to connect")
                        self.master.log(50, "unable to connect wrong user " + self.display_name, self)

                        # if(self.hostname=="#"):
                        #    self.set_hostname(connection)
                        # self.send_command(connection, "terminal len 0", self.hostname)
        else:
            # device has to hop another device
            gateway = CiscoIOS(self.jump_gateway["ip"], "gateway", self.master)
            connection = gateway.connect()
            command = "telnet " + self.ip + "\n"
            command += self.master.username + "\n"
            command += self.master.password + "\n"
            print(gateway.send_command(connection, command, pattern='name:'))

            # print(gateway.send_command(connection, command, pattern='name:'))

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
        result = self.send_command(connection, command_host, "#")
        # print(result)

        lines = result.split("\n")
        for line in lines:
            # print(line + " esta es una linea")
            if line.startswith("hostname"):
                hostname = line.replace("hostname ", "")
                self.hostname = hostname + "#"
                # print(self.hostname + " este es el hostname" )
                return self.hostname
                break
        self.hostname = "#"
        return "#"

    def close(self, connection):
        """
        metodo: close
            :param connection (ConnectHandler): e0s la conexion al equipo
            :return: nada
            llama al metodo ConnectHandler.disconnect() para cerrar el pipeline hacia el equipo
        """
        connection.disconnect()

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
        self.static_routes = {}
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
        '''

        :param address_family(string) default("ipv4 unicast"):
        :return:
        '''
        if not hasattr(self, "bgp_neighbors"):
            self.bgp_neighbors = {}

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

    @staticmethod
    def get_normalize_interface_name(interface_string):
        interface_dict = {"TenGigabitEthernet": "Te",
                          "GigabitEthernet": "Gi",
                          "TenGigE": "Te",
                          "HundredGigE": "Hu",
                          "FortyGigE": "Fo"}

        for pattern, corrected_name in interface_dict.items():
            interface_string = interface_string.replace(pattern, corrected_name)

        return interface_string

    def set_mpls_ldp_interfaces(self, address_family="ipv4 unicast"):
        if not hasattr(self, "ospf_interfaces"):
            # self.set_ip_ospf_interface()
            pass
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
        conn = self.connect()
        show_version = self.send_command(connection=conn, command="show version", timeout=10)
        platform = "CiscoIOS"
        self.platform = platform
        if (show_version.find("IOS XR") > -1):
            platform = "CiscoXR"
        self.platform = platform
        self.close(conn)
        return platform

    def set_jump_gateway(self, ip, protocol):
        self.jump_gateway = {"ip": ip, "protocol": protocol}

    def set_pim_interfaces(self):
        connection = self.connect()
        command = "show "
        show_mpls_interface = self.send_command(connection, command, self.hostname, timeout=5)
        connection = self.connect()
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

    def save_report_sql(self, atribute, report_name="test"):
        # pim_interfaces
        # bgp_neighbors
        # mpls_ldp_interfaces
        # ospf_interfaces

        conn = pmsql.connect("dbname='boip' user='postgres' host='localhost' password='epsilon123'")

        cur = conn.cursor()
        if (hasattr(self, atribute)):
            atribute_dict = getattr(self, atribute)
            table_name = atribute
            for key, row in atribute_dict.items():
                sql_string = "INSERT INTO " + table_name + " ( report_name , local_router_ip," + (",").join(
                    row.keys()) + ") "
                sql_string += " VALUES " + "('" + report_name + "','" + self.ip + "','" + (
                    "','".join(map(str, row.values()))) + "')"
                # print(sql_string)
                last = cur.execute(sql_string)
                conn.commit()
                # print(last)
            pass

    def create_connection(self):
        """ create a database connection to the SQLite database
            specified by db_file
        :param db_file: database file
        :return: Connection object or None
        """
        conn = sql.connect("boip.db")

        return None

    def create_project(self, conn, project):
        """
        Create a new project into the projects table
        :param conn:
        :param project:
        :return: project id
        """
        sql = ''' INSERT INTO projects(name,begin_date,end_date)
                  VALUES(?,?,?) '''
        cur = conn.cursor()
        cur.execute(sql, project)
        return cur.lastrowid

    def create_task(self, conn, task):
        """
        Create a new task
        :param conn:
        :param task:
        :return:
        """

        sql = ''' INSERT INTO tasks(name,priority,status_id,project_id,begin_date,end_date)
                  VALUES(?,?,?,?,?,?) '''
        cur = conn.cursor()
        cur.execute(sql, task)
        return cur.lastrowid

    def set_interface(self, index):
        interface = InterfaceIOS(self, index)
        # print("adentro del metodo",index)
        self.interfaces[index] = interface

    def set_interfaces_stats(self, interfaces_index=[]):
        connection = self.connect()
        if (len(interfaces_index) == 0):
            for index, interface in self.interfaces.items():
                interface.set_stats(connection)
        else:
            for index in interfaces_index:
                if (index in self.interfaces):
                    pass
                else:
                    self.set_interface(index)
                self.interfaces[index].set_stats(connection)
        self.close(connection)

    def get_interfaces_stats(self, interfaces_index=[]):
        output = "";
        for index in interfaces_index:
            if (index in self.interfaces):
                output += self.interfaces[index].get_interface_summary()
        return output

    def set_log(self, filter=""):
        connection = self.connect()
        command = "show logging " + ("" if filter == "" else " | i " + filter)

        self.log = reversed(self.send_command(connection=connection, command=command, timeout=10).split("\n"))
        return self.log

    def get_log(self, filter=""):
        return self.log

    def save_ospf_adjacencies(self):
        self.get_platform()
        self.set_ip_ospf_interfaces()
        interfaces_index = self.ospf_interfaces.keys()
        self.set_interfaces_stats(interfaces_index=interfaces_index)
        db_connection = self.master.connect_mongo()
        collection = db_connection.ospf_adj

        for interface_index, ospf_interface in self.ospf_interfaces.items():
            if ("network_id" in ospf_interface):
                db_result = collection.find_one({'network_id': ospf_interface["network_id"]})
                if (db_result is None):
                    collection.insert_one({'network_id': ospf_interface["network_id"],
                                           'interfaces': [
                                               {
                                                   'ip_neighbor': self.ip,
                                                   'interface_index': interface_index,
                                                   'mtu': self.interfaces[interface_index].mtu,
                                                   'ip_interface': ospf_interface['ospf_ip_address'],
                                                   'network_type': ospf_interface['ospf_net_type'],
                                                   'device_plattform': self.platform

                                               }
                                           ]})
                else:
                    interfaces_list = db_result["interfaces"]
                    flag_in_set = False
                    for interface_data in interfaces_list:
                        if (interface_data["ip_neighbor"] == self.ip):
                            flag_in_set = True

                    if (not flag_in_set):
                        collection.update_one({'network_id': ospf_interface["network_id"]},
                                              {'$push': {
                                                  'interfaces':
                                                      {
                                                          'ip_neighbor': self.ip,
                                                          'interface_index': interface_index,
                                                          'mtu': self.interfaces[interface_index].mtu,
                                                          'ip_interface': ospf_interface['ospf_ip_address'],
                                                          'network_type': ospf_interface['ospf_net_type'],
                                                          'device_plattform': self.platform

                                                      }

                                              }})

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
                protocol = "IP4" if neighbor["bgp_address_family"].find("ipv4") > -1 else "IP6"
                route_map_in = "RMP" + country_key + "IN" + protocol + conection_type + "_" + neighbor[
                    "bgp_description"].replace("|", "_")
                route_map_out = "RMP" + country_key + "IT" + protocol + conection_type + "_" + neighbor[
                    "bgp_description"].replace("|", "_")
                prefix_list = "PFX" + country_key + "IN" + protocol + conection_type + "_" + neighbor[
                    "bgp_description"].replace("|", "_")
                result += "---------------------------------------\n"
                result += "data \n"
                result += "as || " + neighbor["bgp_remote_as"] + " || ip " + ip + "  description " + neighbor[
                    "bgp_description"] + "\n"
                result += "---------------------------------------\n"
                result += "policies\n"
                result += "router bgp 52468 \n"
                result += "address-family " + neighbor["bgp_address_family"] + "\n"
                result += "neighbor " + ip + " route-map " + route_map_in + " in \n"
                result += "\n" if neighbor[
                                      "bgp_policy_out"] == "NA" else "neighbor " + ip + " route-map " + route_map_out + " out \n"
                result += "\nexit\n"
                result += "route-map " + route_map_in + " permit 10\n"
                result += "match ipv6 address prefix-list " + prefix_list + "\n"
                result += "set community 52468:10200 " + neighbor["bgp_remote_as"][
                                                         -5:] + ":52468 52468:1504 52468:20410 52468:20510 52468:20610 52468:20530" + \
                          " 52468:20120 52468:20220 52468:20420 52468:20520 52468:20729   52468:20620) \n"

                result += "\n" if neighbor["bgp_policy_out"] == "NA" else "route-map " + route_map_out + " permit 10\n"
                result += " ipv6 prefix-list " + prefix_list + " permit \n"
                result += self.send_command(connection,
                                            "show run  | s prefix-list " + neighbor["bgp_policy_in"]).replace(
                    neighbor["bgp_policy_in"], prefix_list)

                result += " shows --------\n\n"

                result += "show run  | s route-map " + neighbor["bgp_policy_out"] + "\n\n"

                result += self.send_command(connection, "show run  | s route-map  " + neighbor["bgp_policy_out"])
                result += "\nshow run route-policy " + neighbor["bgp_policy_in"] + "\n\n"
                result += self.send_command(connection, "show run  | s route-map " + neighbor["bgp_policy_in"])
                result += "\n---------------------------------------\n\n"
                result += "show run  | s prefix-list " + neighbor["bgp_policy_out"] + "\n\n"
                result += self.send_command(connection,
                                            "show run  | s prefix-list " + neighbor["bgp_policy_in"]).replace(
                    neighbor["bgp_policy_in"], prefix_list)
                result += "\n---------------------------------------\n\n"
                result += "\n---------------------prefix in ------------------\n\n"
                result += self.send_command(connection, "show run | i prefix-list " + neighbor["bgp_prefix_in"])
                result += "\n---------------------prefix out ------------------\n\n"
                result += self.send_command(connection, "show run | i prefix-list " + neighbor["bgp_prefix_out"])
                result += "\n---------------------------------------\n\n"

        print(result)

    def print_bgp_neighbors(self, address_family="ipv4 unicast"):
        if (hasattr(self, "bgp_neighbors")):
            if not address_family in self.bgp_neighbors:
                self.set_ip_bgp_neighbors(address_family)
        else:
            self.set_ip_bgp_neighbors(address_family)

        columns = []
        output = ""
        for key, neighbor in self.bgp_neighbors.items():
            output = output + key + "!"
            if (len(columns) == 0):
                columns = neighbor.keys()
            for name_column, data_column in neighbor.items():
                output = output + str(data_column) + "!"
            output = output + "\n"
        header = "bgp_ip_neighbor!"
        for column in columns:
            header = header + column + "!"
        output = header + "\n" + output

        return output

    def set_all_interfaces(self):
        command = "show interfaces "
        connection = self.connect()

        show_interfaces = self.send_command(connection, command, self.hostname, timeout=5)
        split_interfaces = show_interfaces.split("swapped out\n")
        interfaces = {}
        for interface in split_interfaces:
            interface_object = InterfaceIOS(self, "NA")
            interface_object.parse_interface_out(interface)
            interfaces[interface_object.index] = interface_object
        self.interfaces = interfaces

    def set_snmp_community(self):

        for community in self.master.communities:
            self.community = community
            self.set_snmp_hostname()
            if self.hostname != "no_snmp":
                break

    def set_snmp_hostname(self):
        community = self.community
        value = "1.3.6.1.2.1.1.5.0"
        cmdGen = cmdgen.CommandGenerator()
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(cmdgen.CommunityData(community),
                                                                           cmdgen.UdpTransportTarget(
                                                                               (self.ip, 161)),
                                                                           value
                                                                           )
        hostname = "no_snmp"
        for name, val in varBinds:
            hostname = str(val).split(".")[0]
        self.hostname = hostname

    def set_snmp_plattform(self):

        platfforms = {"9K": "ASR9K", "ASR920": "ASR920", "900": "ASR900", "default": 'null'}
        cmdGen = cmdgen.CommandGenerator()
        oid = "	1.3.6.1.2.1.1.1"
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.nextCmd(cmdgen.CommunityData(self.community),
                                                                            cmdgen.UdpTransportTarget(
                                                                                (self.ip, 161)),
                                                                            oid
                                                                            )
        plattform = platfforms["default"]
        snmp_value = "null"
        for val in varBinds:
            snmp_value = str(val[0][1]).split("\n")[0]

        for pattern, plattform_name in platfforms.items():
            if (snmp_value.find(pattern) > -1):
                return plattform_name
        self.plattform = plattform

    def set_physical_interfaces(self):
        interfaces_prefixes = ["Te", "Gi", "Hu"]
        command = 'show interfaces description  | e "\\\\." '
        connection = self.connect()
        show_interfaces = self.send_command(connection, command, self.hostname, timeout=5)
        interfaces = {}
        for interface in show_interfaces.split("\n"):
            interface_data = {}
            try:

                interface_split = re.sub(" +", " ", interface).split(" ")
                interface_data["index"] = interface_split[0]
                interface_data["status"] = interface_split[1]
                interface_data["protocol"] = interface_split[2]
                interface_data["description"] = "_".join(interface_split[3:])
                for prefix in interfaces_prefixes:
                    if (interface_data["index"].find(prefix) > -1):
                        interfaces[interface_data["index"]] = interface_data
            except:
                pass
        self.physical_interfaces = interfaces
        return (self.physical_interfaces)

    def set_inventory(self):
        command = "admin show inventory"
        connection = self.connect()
        admin_show_inventory = self.send_command(connection, command, self.hostname, timeout=5)[:-1]
        parts = []
        connection.disconnect()
        for inventory_item in admin_show_inventory.split("\n\n"):
            try:
                part = {}

                lines = inventory_item.replace('"', "").split("\n")

                if (len(lines) > 2):
                    lines = lines[len(lines)-2:]
                part["local_name"] = lines[0].split(",")[0].replace("NAME:", "") \
                    .replace(" module", "") \
                    .replace(" mau ", " ") \
                    .replace("/CPU0", "") \
                    .replace("TenGigE", "") \
                    .replace("GigE", "") \
                    .replace("/SP","")
                part["description"] = lines[0].split(",")[1].replace("DESCR:", "")
                part["PID"] = lines[1].split(",")[0].replace("PID:", "").replace(" ", "")
                part["VID"] = lines[1].split(",")[1].replace("VID:", "").replace(" ", "")

                part["SN"] = lines[1].split(",")[2].replace("SN:", "").replace(" ", "")
                parts.append(part)
                pprint(parts)
            except (Exception):
                print("no able to add line")
                print(lines)
                pass
        self.inventory = parts
        return parts

    def set_chassis(self):
        CiscoPart.create_inventory_tree(self,self.set_inventory())
        return self.chassis


    def draw_device_hardware(self,x,y):
        self.set_chassis()
        print(self.chassis.get_slots_summary(side=0))
        master = Tk()

        canvas = Canvas(master, width=300, height=1000)
        self.chassis.draw_in_canvas(canvas,x,y,recursive=True)
        canvas.pack()



        mainloop()



