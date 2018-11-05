from __future__ import print_function
import re
from netmiko import ConnectHandler
from netmiko import NetMikoTimeoutException
from paramiko import SSHException
import sys
import time
import select
import paramiko


class BaseDevice:

    def __init__(self, Aip, Adisplay_name, Amaster, Aplattform="cisco_device"):
        self.ip = Aip
        self.display_name = Adisplay_name
        self.master = Amaster
        self.hostname = "#"
        self.platfform = Aplattform

    def sendCommand(self, connection, command, pattern="#", read=True, timeout=1):

        output = connection.send_command(command, expect_string=pattern, strip_command=False, delay_factor=timeout)
        return output

    def connect(self, usernamePattern='username', passwordPattern="password", pattern="#"):

        connection = "null"
        try:
            # try ssh

            connection = ConnectHandler(device_type="cisco_ios_ssh", ip=self.ip, username=self.master.username,
                                        password=self.master.password)
            print("ssh conected")
        except (NetMikoTimeoutException, SSHException) as e:
            try:

                connection = ConnectHandler(device_type="cisco_ios_telnet", ip=self.ip, username=self.master.username,
                                            password=self.master.password)
                print("telnet conected")
            except NetMikoTimeoutException:
                print("cannot conect to device")
        return connection
        self.send_command(connection, "terminal len 0", self.hostname)
        self.set_hostname(connection)

        return telnet

    def setHostname(self, connection, AcommandHost="show config | i hostname"):

        result = self.sendCommand(connection, AcommandHost, "#")
        hostname = result.split("\n")[1].replace("hostname ", "")
        self.hostname = hostname + "#"

        return hostname

    def close(self, connection):
        connection.disconnect()

    def setConfig(self, Acommand="show config"):
        connection = self.connect()
        self.config = self.sendCommand(connection, Acommand, self.hostname, timeout=10)

        return self.config

    def setActualConfig(self, Acommand="show run", ):
        connection = self.connect()
        self.config = self.sendCommand(connection, Acommand, self.hostname, timeout=10)
        self.close(connection)
        return self.config

    def setStaticRoute(self, AinVrf=True, AallDistance=True):
        self.setConfig()
        self.staticRoutes = {}
        lineasConfig = self.config.split("\n")
        for index, linea in enumerate(lineasConfig):
            if linea.startswith("ip route vrf"):
                linea = linea.replace("\n", "")
                linea_split = linea.split(" ")
                next_hop = linea_split[6]
                pat = re.compile("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}")
                test = pat.match(next_hop)
                if (test):
                    pass
                else:
                    if (len(linea_split) > 7):
                        next_hop = next_hop = linea_split[7]
                    else:
                        next_hop = "null"
                if (next_hop != "null"):
                    route = linea_split[4]
                    mask = linea_split[5]
                    vrf = linea_split[3]

                    self.staticRoutes[next_hop + vrf] = [vrf, route, mask, next_hop, linea]
        return self.staticRoutes

    def getRecursiveRoutes(self):
        self.setStaticRoute()
        command = ""
        connection = self.connect()
        print("trabajando... muchas rutas..")
        for key, route in self.staticRoutes.items():

            showroute = self.sendCommand(connection, "\n" + "show ip route vrf " + route[0] + " " + route[3] + " \n",
                                         timeout=2)
            if (showroute.find("default") != -1):
                command += "no " + route[4] + "\n"

        return command
