import ipaddress

class InterfaceIOS(object):
    def __init__(self, parent_device, parse_data):
        self.id = 0
        self.parent_device = parent_device
        self.index = ""
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

        try:
            self.util_in, self.util_out = self.util()
        except:
            self.util_in = 0

        try:
            self.ip = ipaddress.ip_interface(self.ip).ip
            self.netmask = ipaddress.ip_interface(self.ip).netmask
        except:
            self.ip = ipaddress.ip_address("127.0.0.1")
            self.netmask = ipaddress.ip_interface("127.0.0.1/32").netmask


    def util(self):

        real_bw = float(self.bw) * 1024
        if ("Hu" in self.index):
            real_bw = 100000000000
        if ("Te" in self.index):
            real_bw = 10000000000
        if ("Gi" in self.index):
            real_bw = 1000000000

        util_in = round(float(self.input_rate) / real_bw * 100, 2)
        util_out = round(float(self.output_rate) / real_bw * 100, 2)
        return util_in, util_out

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

        output = "|INT[" + self.index + "]"
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
        return str(id(self)) + str(self.__class__) + self.index + " " + self.description + " " + self.link_state + " "

    def __repr__(self):
        return str(id(self)) + str(self.__class__) + self.index + " " + self.description + " " + self.link_state + " "
