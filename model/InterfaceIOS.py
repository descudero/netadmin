import ipaddress


class InterfaceIOS:
    def __init__(self, parent_device, index):
        self.parent_device = parent_device
        self.index = index
        self.set_initial_stats()
        pass

    def set_initial_stats(self):
        self.phy_state = "DOWN"
        self.protocol_state = "DOWN"
        self.hardware_type = "NA"
        self.mac_address = "aaaa.aaaa.aaaa"
        self.description = "null"
        self.mtu = "1500"
        self.bw = 1
        self.duplex = "NA"
        self.last_clear_counters = "0"
        self.output_drops = "0"
        self.rate_in = "0"
        self.rate_out = "0"
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

    def parse_interface_out(self, show_output):

        lines_show_ouput = show_output.split("\n")
        duplex_set = False

        for linea in lines_show_ouput:
            # print(linea)
            if linea.find("line protocol") != -1:
                index = linea.split(" ")[0]
                self.index = InterfaceIOS.get_normalize_interface_name(index)
                dict_states = {"administratively down": "ADMIN_DOWN", "up": "UP"}
                states_interfaces_split = linea.split(",")
                for state, save_state in dict_states.items():
                    if states_interfaces_split[0].find(state) > -1:
                        self.phy_state = save_state
                if states_interfaces_split[0].find("up"):
                    self.protocol_state = "UP"
            if linea.find("Description") != -1:
                self.description = linea.replace("  Description: ", "")
            if linea.find("Hardware") != -1 and linea.find(", address is") != -1:
                # print(linea.split(", address is"))
                self.mac_address = linea.split(", address is")[1].split(" ")[0]
            if linea.find("Internet address is ") != -1:
                ip = linea.replace("Internet address is ", "").replace(" ", "")
                self.ip = ipaddress.ip_address(ip.split("/")[0])
                self.network = ipaddress.ip_network(ip, False)

            if linea.find("MTU") != -1:
                self.mtu = linea.split(",")[0].replace("MTU ", "").replace(" bytes", "").replace(" ", "")
            if linea.find(", BW") != -1:
                # print(linea)

                if (linea.find("not configured") > -1):
                    self.bw = 0
                else:
                    self.bw = int(linea.split(", BW")[1].split(" ")[1])
                # print(self.bw)
            if linea.find("-duplex") != -1 and duplex_set == False:
                split_linea = linea.split(",")
                self.duplex = split_linea[0].replace(" ", "")
                self.speed = split_linea[1].replace(" ", "")
                duplex_set = True
                if len(split_linea) > 2:
                    self.transport_type = split_linea[2]
                else:
                    self.transport_type = "bundle"
            if linea.find("input rate") != -1:
                self.rate_in = int(linea.split("input rate ")[1].split(" ")[0].replace(" ", ""))
            if linea.find("output rate") != -1:
                self.rate_out = int(linea.split("output rate ")[1].split(" ")[0].replace(" ", ""))
            if linea.find("input_drops") != -1:
                self.input_drops = linea.split(";")[-1].replace(" Total input drops", "").replace("")
            if linea.find("output drops") != -1:
                self.output_drops = linea.split("Total output drops: ")[-1].replace(" ", "")

            if linea.find('throttles') != -1:
                # runts giants throthles

                runts_lines = linea.split(",")
                self.runts = runts_lines[0].replace("runts", "").replace(" ", "")
                self.giants = runts_lines[1].replace("giants", "").replace(" ", "")
                self.throttles = runts_lines[2].replace("throttles", "").replace(" ", "")

            if linea.find('input errors') != -1:
                # input errors, CRC, frame, overrun,ignored.
                input_error_lines = linea.split(",")
                self.input_errors = input_error_lines[0].replace("input errors", "").replace(" ", "")
                self.crc = input_error_lines[1].replace("CRC", "").replace(" ", "")
                self.frame = input_error_lines[2].replace("frame", "").replace(" ", "")
                self.overrun = input_error_lines[3].replace("overrun", "").replace(" ", "")
                self.ignored = input_error_lines[4].replace("ignored", "").replace(" ", "")

            if linea.find('output errors') != -1:
                # output errors interfaces resets
                output_error_lines = linea.split(",")
                self.output_errors = output_error_lines[0].replace("output errors", "").replace(" ", "")
            if linea.find('Last clearing of ') != -1:
                self.last_clear_counters = linea.split(" counters ")[1]

        self.utilization_in = 0 if self.bw == 0 else round(float(self.rate_in) / (float(self.bw * 10)), 2)
        self.utilization_out = 0 if self.bw == 0 else round(float(self.rate_out) / (float(self.bw * 10)), 2)

    def set_stats(self, connection, command="show interface "):
        show_interface_output = connection.send_command(command + self.index)
        self.parse_interface_out(show_interface_output)

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
