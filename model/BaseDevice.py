from __future__ import print_function
import re
from netmiko import ConnectHandler
from netmiko import NetMikoTimeoutException
from netmiko import NetMikoAuthenticationException
import sys
import time
import select
import paramiko
import textfsm


class BaseDevice(object):

    def __init__(self, ip, display_name, master, platform="CiscoIOS", gateway="null"):
        self.ip = ip
        self.display_name = display_name
        self.master = master
        self.hostname = "#"
        self.platform = platform
        self.interfaces_stats_set = False
        self.interfaces = {}
        self.log = []
        self.gateway = gateway

    def __str__(self):
        return self.display_name + " " + self.ip
    def send_command(self, connection, command, pattern="#", read=True, timeout=1):

        print(command)
        output = connection.send_command(command,
                                         expect_string=pattern,
                                         strip_command=False,
                                         delay_factor=timeout)
        return output

    def connect(self, usernamePattern='username', passwordPattern="password", pattern="#"):

        try:
            # try ssh
            connection = ConnectHandler(device_type="cisco_ios_telnet", ip=self.ip, username=self.master.username,
                                        password=self.master.password)
            print("telnet conected")

        except NetMikoTimeoutException:
            try:

                connection = ConnectHandler(device_type="cisco_ios_ssh", ip=self.ip, username=self.master.username,
                                            password=self.master.password)
                print("ssh conected " + self.display_name)
            except NetMikoAuthenticationException:
                print("contrasena o usuario incorrecto")

        return connection
        self.send_command(connection, "terminal len 0", self.hostname)
        self.set_hostname(connection)

        return telnet

    def set_hostname(self, connection, AcommandHost="show config | i hostname"):

        result = self.send_command(connection, AcommandHost, "#")
        hostname = result.split("\n")[1].replace("hostname ", "")
        self.hostname = hostname + "#"

        return hostname

    def close(self, connection):
        connection.disconnect()

    def set_config(self, Acommand="show config"):
        connection = self.connect()
        self.config = self.send_command(connection, Acommand, self.hostname, timeout=10)

        return self.config

    def setActualConfig(self, Acommand="show run", ):
        connection = self.connect()
        self.config = self.send_command(connection, Acommand, self.hostname, timeout=10)
        self.close(connection)
        return self.config

    def load_template(self, template_name):
        if not "template" in template_name:
            template_name += ".template"
        parser = textfsm.TextFSM(open("./resources/templates/" + template_name))
        return parser
