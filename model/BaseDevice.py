from __future__ import print_function
import re
from netmiko import ConnectHandler
from netmiko import NetMikoTimeoutException
from netmiko import NetMikoAuthenticationException
import time
import textfsm
import socket
import os
from platform import system as system_name  # Returns the system/OS name
from subprocess import call   as system_call  # Execute a shell command
from tools import logged


@logged
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
        self.able_connect = False

    def log_performance(self, function_to_logtime):
        start_test = time.time()

        def wrapper(*args, **kwargs):
            output = function_to_logtime(*args, **kwargs)

        end_test = time.time()
        self.master.log_time(30, start_test, end_test, self, print_function)
        return wrapper



    def __str__(self):
        return self.display_name + " " + self.ip

    def send_command(self, command, connection=None, pattern="#", read=True, timeout=1):
        if (connection is None):
            connection = self.connect()

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

    def set_hostname(self, connection, AcommandHost="show config | i hostname"):

        result = self.send_command(connection, AcommandHost, "#")
        hostname = result.split("\n")[1].replace("hostname ", "")
        self.hostname = hostname + "#"

        return hostname

    def close(self, connection):
        self.logger_connection.info("{0} close() ".format(self.ip))
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

        with open("./resources/templates/" + template_name) as template_text:
            try:
                parser = textfsm.TextFSM(template_text)
                return parser
            except Exception as e:
                self.dev.error("unable to load template {0} err {1}".format(template_name, repr(e)))

        return 0

    def parse_txtfsm_template(self, template_name, text):
        parser = self.load_template(template_name=template_name)
        try:
            fsm_results = parser.ParseText(text)
            header = [column.lower() for column in parser.header]
            return [dict(zip(header, row)) for row in fsm_results]
        except Exception as e:
            self.dev.critical("{0} Unable to parse data {1} template (2) ".format(self.ip, repr(e), template_name))
            self.verbose.critical("{0} Unable to parse data {1} template (2) ".format(self.ip, repr(e), template_name))
            return []

    def send_command_and_parse(self, command, template_name, timeout=5, close_connection=True):

        connection = self.connect()

        cli_output = self.send_command(connection=connection, command=command, timeout=timeout)
        connection.disconnect()
        self.verbose.debug("{0} comm {1} cli {2}".format(self.ip, template_name, cli_output))

        return self.parse_txtfsm_template(template_name=template_name, text=cli_output)



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
        return self.able_telnet

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

        if system_name().lower() == 'windows':
            self.device_up = system_call(command, shell=True) == 0
        else:
            self.device_up = os.system(f"ping -c 2  -W 1 {self.ip} ") == 0
        # Pinging
        return self.device_up

    def __repr__(self):
        return str(self.__class__) + " " + self.ip
