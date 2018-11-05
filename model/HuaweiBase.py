from __future__ import print_function

from netmiko import ConnectHandler
from netmiko import NetMikoAuthenticationException
from netmiko import NetMikoTimeoutException

from model.BaseDevice import BaseDevice as Parent


class HuaweiBase(Parent):

    def __init__(self, Aip, Adisplay_name, Amaster, Aplattform="cisco_ios_telnet"):
        self.ip = Aip
        self.display_name = Adisplay_name
        self.master = Amaster
        self.hostname = "#"
        self.platfform = Aplattform

    def connect(self, username_pattern='username', password_pattern="password", pattern=">"):

        connection = "null"
        try:
            connection = ConnectHandler(device_type="cisco_ios_telnet",
                                        ip=self.ip, username=self.master.username,
                                        password=self.master.password)
            print("ssh conected " + self.display_name)

        except (NetMikoTimeoutException) as e:
            try:

                # try ssh
                connection = ConnectHandler(device_type="huawei",
                                            protocol="ssh"
                                            , ip=self.ip,
                                            username=self.master.username,
                                            password=self.master.password)
                print("telnet conected " + self.display_name)


            except NetMikoAuthenticationException:
                print("contrasena o usuario incorrecto")

        self.send_command(connection, "screen-length 0 temporary", self.hostname)

        return connection

    def sendCommand(self, connection, command, pattern=">", read=True, timeout=1):

        output = connection.send_command(command, expect_string=">", strip_command=False, delay_factor=timeout)
        return output
