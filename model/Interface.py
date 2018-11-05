import ipaddress


# from kivy.uix.boxlayout import BoxLayout
# from LabelB import LabelB


class Interface:
    # description TAG:ROJO ! CP:40GB ! EBGP:COGENT ! PEER:38.88.165.53 !
    #  EBGPID:CIRCUIT-ID 1-300032199 ! TX:AMX ! TXID:CABLE AMX-1 -REMOTE EQ ROUTER
    # 21.MIA03 ID-AMX IAM1GTIZPPBR-USFLMNAP-GE10-005
    #
    def __init__(self,
                 index,
                 description,
                 tag,
                 peer,
                 ebgp,
                 ebgpid,
                 tx,
                 txid):
        # el index de la interfaz es el nombre como tal ejemplo Ten1/1 Gi1/1 etc
        self.index = index
        # la descripcion
        self.description = description
        # estos ton atributos de interfaces con PEERS de internet seran extendidos en su momento
        self.stats_Set = False

    def __str__(self):
        # extendemos la clase de objeto para mostrar un forma mas apropiada el to string
        return self.index + " " + self.description

    def get_service_policy_rate(self, connection, parentDevice, Acommand="show policy-map interface "):
        if hasattr(self, "policy_map_rate"):
            return self.policy_map_rate
        # print("pensando demasiadas interfaces")
        command_in = Acommand + self.index + " input "
        command_out = Acommand + self.index + " output "
        # se utilizan varias variables de la interfaz como tal para el retorno de la informacion
        # por lo que se necesita
        if not self.stats_Set:
            self.set_interface_stats(connection, parentDevice)

        # se crea un dicccionario con in y out de llaves por las direcciones de los policies

        policymap_rate = {}
        # se envian los comandos unicos al dispositivo cisco dependiendeo de la orientacion de la interfaz
        in_show = parentDevice.send_command(connection,
                                            command_in,
                                            parentDevice.hostname,
                                            timeout=.5)
        out_show = parentDevice.send_command(connection,
                                             command_out,
                                             parentDevice.hostname,
                                             timeout=.5)
        # si estan instalados en la interfaz es decir que no tiene el texto mencionado se envian al metodo para analizar
        if in_show.find("not installed") == -1:
            policymap_rate["in"] = self.analize_policy(in_show)
        if out_show.find("not installed") == -1:
            policymap_rate["out"] = self.analize_policy(out_show)
        self.policy_map_rate = policymap_rate
        return policymap_rate

    def set_interface_stats(self, connection, parentDevice, Acommand="show interface "):
        print("pensando %")
        show_interface = parentDevice.send_command(connection,
                                                   Acommand + self.index,
                                                   parentDevice.hostname, timeout=.2)
        # print(show_interface)

        lineas_show = show_interface.split("\n")
        # se inicia un set inicial de las propiedades de la interfaz
        self.operational_state = "down"
        self.admin_state = "down"
        self.mac_address = "0000.0000.0000"
        self.ip = ipaddress.ip_address("127.0.0.1")
        self.mtu = "1500"
        self.bandwith = 0
        self.duplex = "Full"
        self.speed = "10"
        self.input_rate = 0
        self.output_rate = 0
        self.input_drops = 0
        self.output_drops = 0
        self.runts = 0
        self.giants = 0
        self.throttles = 0
        self.input_errors = 0
        self.crc = 0
        self.frame_error = 0
        self.overrun = 0
        self.transport_type = ""
        duplex_set = False
        # se parsea la interfaz con diferentes variables.
        for linea in lineas_show:
            # print(linea)
            if linea.find("line protocol") != -1:
                states_split = linea.split(",")
                self.admin_state = states_split[0].split(" ")[-1]
                self.operational_state = states_split[1].split(" ")[-1]
            if linea.find("Hardware") != -1 and linea.find(", address is") != -1:
                print(linea.split(", address is"))
                self.mac_address = linea.split(", address is")[1].split(" ")[0]
            if linea.find("Internet address is ") != -1:
                ip = linea.replace("Internet address is ", "").replace(" ", "")
                self.ip = ipaddress.ip_address(ip.split("/")[0])
                self.network = ipaddress.ip_network(ip, False)

            if linea.find("MTU") != -1:
                self.mtu = linea.split(",")[0].replace("MTU ", "").replace(" bytes", "")
            if linea.find(", BW") != -1:
                self.bandwith = int(linea.split(", BW")[1].split(" ")[1])
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
                self.input_rate = int(linea.split("input rate ")[1].split(" ")[0].replace(" ", ""))
            if linea.find("output rate") != -1:
                self.output_rate = int(linea.split("output rate ")[1].split(" ")[0].replace(" ", ""))
            if linea.find("input_drops") != -1:
                self.input_drops = int(linea.split(",")[-1].replace(" total input drops", "").replace(""))
            if linea.find("output_drops") != -1:
                self.output_drops = int(linea.split(",")[-1].replace(" total output drops", "").replace(""))
            if linea.find('input errors') != -1:
                linea_split = linea.split(",")
                self.input_errors = int(linea_split[0].replace("input errors", "").replace(" ", ""))
                print(linea_split[1])
                print(linea_split[1].replace(" CRC", ""))
                self.crc = int(linea_split[1].replace(" ", "").replace("CRC", ""))
                self.frame_error = int(linea_split[2].replace("frame", "").replace(" ", ""))
                self.overrun = int(linea_split[3].replace("overrun", "").replace(" ", ""))
        self.stats_Set = True

    def analize_policy(self, output):
        # este metodo esta disenado para analizar policies de XR
        # print(output)
        classes_q_o_s = output.split("Class ")
        classes_q_o_s.pop(0)
        class_rate = {}
        # el ancho de banda esta calculado con 1024 kbit en 1 mb y 1024 mbit en un 1 gbs
        bw = round(self.bandwith / 1024 / 1024, 2)
        print("bandwith" + str(bw))
        # de igual forma se asigna en la llaves por consistencia
        class_rate["bw"] = {"transmited": bw, "match": bw, "dropped": bw}
        # se crea un acumulador para tener la clase total
        total = {"transmited": 0, "match": 0, "dropped": 0}
        # print(classesQOS)
        for class_qos in classes_q_o_s:
            # print(class_qos)
            lines = class_qos.split("\n")
            class_name = lines[0]
            class_match = round(float(lines[2][67:].replace(" ", "")) / 1024 / 1024, 3)
            class_transmited = round(float(lines[3][67:].replace(" ", "")) / 1024 / 1024, 3)
            class_dropped = round(float(lines[4][67:].replace(" ", "")) / 1024 / 1024, 3)
            class_rate[class_name] = {"match": class_match, "transmited": class_transmited, "dropped": class_dropped}
            total["transmited"] += class_transmited
            total["match"] += class_match
            total["dropped"] += class_dropped
        class_rate["total"] = total
        # se crea la llave % para el porcentaje de utilizacion total de la interfaz
        class_rate["%"] = {"transmited": total["transmited"] / class_rate["bw"]["transmited"],
                           "match": total["match"] / class_rate["bw"]["match"],
                           "dropped": total["dropped"] / class_rate["bw"]["dropped"]}

        return class_rate


"""
    def get_kivy_policy_rate(self, connection, parent_device, keys):
        interface_layout = BoxLayout(orientation="horizontal",spacing=2)
        interface_layout.size_hint_x=1
        label_index = LabelB(text=self.index.replace("GigE","").replace("dred",""),font_size=12,bcolor=[0.5, 0.3, 0.2, 0.25],size_hint=(0.05,1))

        label_index.size_hint = (0.16,1)
        label_tag = LabelB(text=self.tag,font_size=12,bcolor=[0.6, 0.3, 0.2, 0.25])
        label_tag.size_hint = (0.14, 1)
        interface_layout.add_widget(label_index)
        interface_layout.add_widget(label_tag)

        if not hasattr(self, "policy_map_rate"):
            self.get_service_policy_rate(connection=connection, parentDevice=parent_device)
        directions = ["in", "out"]
        for direction in directions:
            policy_direction_layout = BoxLayout(orientation="horizontal",spacing=2)
            if direction in self.policy_map_rate:
                for index in keys[direction]:
                    values = self.policy_map_rate[direction][index]
                    colors = Interface.get_kivy_label_usage_color(index=index,
                                                             value=values["transmited"],
                                                             bw=self.policy_map_rate[direction]["bw"]["transmited"],
                                                             total=self.policy_map_rate[direction]["total"]["transmited"])

                    policy_direction_layout.add_widget(LabelB(text=str(round(values["transmited"], 2)),
                                                              font_size=12,
                                                              bcolor=colors["color"],
                                                              color=colors["font_color"]))
            interface_layout.add_widget(policy_direction_layout)

        return interface_layout

    @staticmethod
    def get_kivy_label_usage_color( index, value, bw, total,opacity=.5):

        color = [0.5, 0.5, 0.5, opacity]
        font_color = [1, 1, 1, 1]
        level = .5
        percentage_uso = .2
        
        if index == "bw":
            color=[0.3, 0.3, 1, opacity]
        else:
            if round(value, 2) == 0:
                color = [0, 0, 0, 0]
                font_color = [0, 0, 0, 0]
            else:
                if index != "bw" and index != "%" and index != "total":
                    percentage_uso = round(value
                                           / total,
                                           2)
                elif index == "total":
                    percentage_uso = round(value
                                           / bw,
                                           2)

                elif index == "%":
                    percentage_uso = round(value, 2)

                if level <= percentage_uso and index != "bw":
                    variable = (1 - (percentage_uso - .5) * 2)
                    # print("color variable ", variable)
                    color = [1, variable, 0, opacity]
                else:
                    variable = (1 - (.5 - percentage_uso) * 2)
                    # print("color variable ", variable)
                    color = [variable, 1, 0, opacity]
        return {"color": color, "font_color": font_color}
"""


class InternetInterface(Interface):
    def __init__(self,
                 index,
                 description,
                 tag,
                 peer,
                 ebgp,
                 ebgpid,
                 tx,
                 txid):
        # el index de la interfaz es el nombre como tal ejemplo Ten1/1 Gi1/1 etc
        self.index = index
        # la descripcion
        self.description = description
        # estos ton atributos de interfaces con PEERS de internet seran extendidos en su momento
        self.tag = tag
        self.peer = peer
        self.ebgp = ebgp
        self.ebgpid = ebgpid
        self.tx = tx
        self.txid = txid
        self.stats_Set = False

    def get_ebgp_route_policy(self):
        # este es un metodo especifico para interfaz de IPP la cual tiene como objetivo
        # regresar el nombre de la polica de bgp
        return "policy_nbr_".join(self.peer.replace(".", "_")).join("_ipv4_unicast_out")

    def get_service_policy_name(self):
        pass
