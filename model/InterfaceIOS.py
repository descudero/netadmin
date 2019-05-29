import ipaddress
from collections import OrderedDict
from tools import logged


@logged
class InterfaceIOS(object):
    def __init__(self, parent_device, parse_data):
        self.uid = 0
        self.parent_device = parent_device
        self.if_index = ""
        self.link_state = "DOWN"
        self.protocol_state = "DOWN"
        self.hardware_type = "NA"
        self.mac_address = "aaaa.aaaa.aaaa"
        self.bia = "aaaa.aaaa.aaaa"
        self.description = "null"
        self.media_type = "null"
        self.mtu = "1500"
        self.bw = 0
        self.duplex = "NA"
        self.delay = "NA"
        self.last_reset = "0"
        self.output_drops = "0"
        self.input_rate = "0"
        self.output_rate = "0"
        self.input_packets = "0"
        self.output_packets = "0"
        self.runts = "0"
        self.giants = "0"
        self.throttles = "0"
        self.input_errors = "0"
        self.crc = "0"
        self.frame = "0"
        self.overrun = "0"
        self.ignored = "0"
        self.underruns = "0"
        self.output_errors = "0"
        self.collisions = "0"
        self.interfaces_resets = "0"
        self.babbles = "0"
        self.late_collision = "0"
        self.deferred = "0"
        self.lost_carrier = "0"
        self.no_carrier = "0"
        self.pause_output = "0"
        self.utilization_in = "0"
        self.utilization_out = "0"
        self.ip = "na"
        self.speed = "na"

        for key, value in parse_data.items():
            if not value == '':
                setattr(self, key, value)
        self.if_index = InterfaceIOS.get_normalize_interface_name(self.if_index)
        self.correct_bw()
        try:
            self.util_in, self.util_out = self.util()
        except:
            self.util_in = 0
            self.util_out = 0

        try:
            self.ip = ipaddress.ip_interface(self.ip).ip
            self.netmask = ipaddress.ip_interface(self.ip).netmask
        except:
            self.ip = ipaddress.ip_address("127.0.0.1")
            self.netmask = ipaddress.ip_interface("127.0.0.1/32").netmask

    def correct_bw(self):

        if "BVI" in self.if_index:
            self.bw = 10_000_000_000
        elif "Hu" in self.if_index:
            self.bw = 100_000_000_000
        elif "Te" in self.if_index:
            self.bw = 10_000_000_000
        elif "Gi" in self.if_index:
            self.bw = 1_000_000_000

    def util(self):

        try:
            util_in = round(float(self.input_rate) / self.bw * 100, 2)
        except TypeError as te:
            util_in = 0
            self.dev.info(f'{self.parent_device} {self.if_index} interface util no able to set until_in')
        try:
            util_out = round(float(self.output_rate) / self.bw * 100, 2)
        except TypeError as te:
            util_out = 0
            self.dev.info(f'{self.parent_device} {self.if_index} interface util no able to set until_out ')
        return 100 if util_in > 100 else util_in, 100 if util_out > 100 else util_out

    def get_interface_errors(self, filter="0"):
        list_properties_erros = ["output_drops", "runts", "giants", "throttles", "input_errors", "crc"
            , "frame", "overrun", "ignored", "underruns", "output_errors"
            , "collisions", "babbles", "late_collision"
            , "deferred", "lost_carrier", "no_carrier", "pause_output"]
        filtered_errors = {}
        for error_key in list_properties_erros:
            error_value = getattr(self, error_key)
            # print("err key", error_key, ":", error_value)
            if (error_value != filter):
                filtered_errors[error_key] = error_value
        return filtered_errors

    def get_interface_summary(self, status=False):

        description = self.description[0:20] if len(self.description) > 21 else self.description

        output = "|INT[" + self.if_index + "]"
        if (status == False):
            output += "| phy [" + self.phy_state + "]| pro [" + self.protocol_state + "] "
        output += "|MTU[" + self.mtu + "]"
        output += "|DES[" + description + "]"
        output += "|DUP [" + self.duplex + "]|SP[" + self.speed + "] "
        output += "|RATEIN[" + str(self.utilization_in) + "%]|RATEOUT[" + str(self.utilization_out) + "%]"
        errors = self.get_interface_errors()
        output += "|ERR:{"
        for key_error, error in errors.items():
            output += " " + key_error + ": [" + str(error) + "] ;"
        output += "}|\n"
        return output

    @staticmethod
    def get_interfaces(conection, device):

        command = "show interfaces"
        # output = device.send_command(connection=conection,command=)

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

    def __str__(self):
        s = f'{id(
            self)}  {self.__class__} u:{self.uid} {self.if_index} L:{self.protocol_state} P:{self.link_state} {self.description}'
        return s

    def __repr__(self):
        s = f'{id(
            self)}  {self.__class__}  u:{self.uid} {self.if_index} L:{self.protocol_state} P:{self.link_state} {self.description}'
        return s

    @property
    def dict(self):
        return self.dict_data()

    def dict_data(self):
        interface_data = dict()
        interface_data['if_index'] = self.if_index
        interface_data['ip'] = str(self.ip)
        interface_data['speed '] = self.speed
        interface_data['util_in'] = self.util_in
        interface_data['util_out'] = self.util_out
        interface_data['description '] = self.description
        interface_data['mtu '] = self.mtu
        interface_data['link_state '] = self.link_state
        interface_data['protocol_state '] = self.protocol_state
        interface_data['hardware_type '] = self.hardware_type
        interface_data['mac_address '] = self.mac_address
        interface_data['bia '] = self.bia
        interface_data['media_type '] = self.media_type
        interface_data['bw '] = self.bw
        interface_data['duplex '] = self.duplex
        interface_data['delay '] = self.delay
        interface_data['last_reset '] = self.last_reset
        interface_data['output_drops '] = self.output_drops
        interface_data['input_rate '] = self.input_rate
        interface_data['output_rate '] = self.output_rate
        interface_data['input_packets '] = self.input_packets
        interface_data['output_packets '] = self.output_packets
        interface_data['runts '] = self.runts
        interface_data['giants '] = self.giants
        interface_data['throttles '] = self.throttles
        interface_data['input_errors '] = self.input_errors
        interface_data['crc '] = self.crc
        interface_data['frame '] = self.frame
        interface_data['overrun '] = self.overrun
        interface_data['ignored '] = self.ignored
        interface_data['underruns '] = self.underruns
        interface_data['output_errors '] = self.output_errors
        interface_data['collisions '] = self.collisions
        interface_data['interfaces_resets '] = self.interfaces_resets
        interface_data['babbles '] = self.babbles
        interface_data['late_collision '] = self.late_collision
        interface_data['deferred '] = self.deferred
        interface_data['lost_carrier '] = self.lost_carrier
        interface_data['no_carrier '] = self.no_carrier
        interface_data['pause_output '] = self.pause_output

        return interface_data
