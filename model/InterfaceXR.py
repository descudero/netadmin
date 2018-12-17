import ipaddress

from model.InterfaceIOS import InterfaceIOS as Parent


class InterfaceXR(Parent):

    def parse_interface_out(self, show_output):
        lines_show_ouput = show_output.split("\n")
        duplex_set = False
        self.ip = ipaddress.ip_address("172.0.0.1")
        try:

            for linea in lines_show_ouput:

                if linea.find("line protocol") != -1:
                    index = linea.split(" ")[0]
                    self.index = Parent.get_normalize_interface_name(index)
                    dict_states = {"administratively down": "ADMIN_DOWN", "up": "UP"}
                    states_interfaces_split = linea.split(",")
                    for state, save_state in dict_states.items():
                        if states_interfaces_split[0].find(state) > -1:
                            self.phy_state = save_state
                    if states_interfaces_split[0].find("up"):
                        self.protocol_state = "UP"
                if linea.find("Description") != -1:
                    # print("Description")
                    self.description = linea.replace("  Description: ", "")

                if linea.find("Hardware") != -1 and linea.find(", address is") != -1:
                    # print("Descriptiom")
                    # print(linea.split(", address is"))
                    self.mac_address = linea.split(", address is")[1].split(" ")[0]
                if linea.find("Internet address is ") != -1:
                    # print("ip")

                    ip = linea.replace("Internet address is ", "").replace(" ", "")
                    try:
                        self.ip = ipaddress.ip_address(ip.split("/")[0])
                        self.network = ipaddress.ip_network(ip, False)
                    except Exception:
                        self.ip = ipaddress.ip_address("172.0.0.1")
                        self.network = "0.0.0.0"
                if linea.find("MTU") != -1:
                    # print("MTU")
                    self.mtu = linea.split(",")[0].replace("MTU ", "").replace(" bytes", "").replace(" ", "")
                if linea.find(", BW") != -1:
                    self.bw = int(linea.split(", BW")[1].split(" ")[1])
                    # print("BW", self.bw)
                if linea.find("duplex") != -1 and duplex_set == False:
                    split_linea = linea.split(",")
                    self.duplex = split_linea[0]
                    self.speed = split_linea[1]
                    duplex_set = True
                    if len(split_linea) > 2:
                        self.transport_type = split_linea[2]
                    else:
                        self.transport_type = "bundle"
                if linea.find("input rate") != -1:
                    self.rate_in = int(linea.split("input rate ")[1].split(" ")[0].replace(" ", ""))
                    # print(self.rate_in)
                if linea.find("output rate") != -1:
                    self.rate_out = int(linea.split("output rate ")[1].split(" ")[0].replace(" ", ""))

                    # print(self.rate_out)
                if linea.find("input_drops") != -1:
                    self.input_drops = int(linea.split(",")[-1].replace(" total input drops", "").replace(""))
                if linea.find("output_drops") != -1:
                    self.output_drops = int(linea.split(",")[-1].replace(" total output drops", "").replace(""))
                if linea.find('input errors') != -1:
                    linea_split = linea.split(",")
                    self.input_errors = int(linea_split[0].replace("input errors", "").replace(" ", ""))
                    self.crc = int(linea_split[1].replace(" ", "").replace("CRC", ""))
                    self.frame_error = int(linea_split[2].replace("frame", "").replace(" ", ""))
                    self.overrun = int(linea_split[3].replace("overrun", "").replace(" ", ""))
                    self.ignored = linea_split[4].replace("ignored", "").replace(" ", "")

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
        except Exception:
            print(show_output)
        try:
            self.util_in = round(float(self.rate_in) / (float(self.bw * 10)), 2)

        except:
            # print(self.parent_device,"unable to set rate in ," + self.rate_in, self.bw)
            self.util_in = 0
        try:
            self.util_out = round(float(self.rate_out) / (float(self.bw * 10)), 2)
        except:
            # print(self.parent_device,"unable to set rate in ," + self.rate_out, self.bw)
            self.util_out = 0
    def __str__(self):
        return self.index + " " + self.phy_state + " "
