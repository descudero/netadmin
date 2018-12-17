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
import socket

from platform import system as system_name  # Returns the system/OS name
from subprocess import call   as system_call  # Execute a shell command

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

    def log_performance(self, function_to_logtime):
        start_test = time.time()

        def wrapper(*args, **kwargs):
            output = function_to_logtime(*args, **kwargs)

        end_test = time.time()
        self.master.log_time(30, start_test, end_test, self, print_function)
        return wrapper



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

    def send_command_and_parse(self, command, template_name, timeout=5, close_connection=True):
        connection = self.connect()
        cli_output = self.send_command(connection=connection, command=command, timeout=timeout)
        connection.disconnect()
        parser = self.load_template(template_name=template_name)
        fsm_results = parser.ParseText(cli_output)
        header = [column.lower() for column in parser.header]
        return [dict(zip(header, row)) for row in fsm_results]

    def set_jump_gateway(self, ip, protocol):
        self.jump_gateway = {"ip": ip, "protocol": protocol}

    def check_ssh(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((self.ip, 22))
        self.able_ssh = result == 0
        return self.able_ssh

    def check_telnet(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((self.ip, 23))
        self.able_telnet = result == 0
        return self.able_telne

    def check_able_connect(self):
        self.able_connect = (self.check_device_up() and (
                self.check_ssh() or self.check_telnet()))
        return self.able_connect

    def check_device_up(self):

        """
            Returns True if host (str) responds to a ping request.
            Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
            """

        # Ping command count option as function of OS
        param1 = '-n' if system_name().lower() == 'windows' else '-c'
        param2 = '-w' if system_name().lower() == 'windows' else '-W'
        # Building the command. Ex: "ping -c 1 google.com"
        command = ['ping', param2, '200', param1, '1', self.ip]
        self.device_up = system_call(command, shell=True) == 0
        # Pinging
        return self.device_up

    def __repr__(self):
        return str(self.__class__) + " " + self.ip
