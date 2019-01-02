from model.InterfaceIOS import InterfaceIOS
import re
from itertools import islice


class InterfaceUfinet(InterfaceIOS):
    '''
    This interface ins to accomodate the standard for clasificacion of the interface, and give some special attributtes via
    description of the interface:
    l3_rotocol
    L1_conection
    '''
    directions = {"D": "DOWNSTREAM",
                  "U": "UPSTREAM",
                  "B": "BOTH"}

    l1_converter = {"D": {"DATA": "DWDM",
                          "P": "PATEC",
                          "N": "NOKIA"},
                    "C": {"DATA": "CABLE_SUBMARINO",
                          "M": "MAYA",
                          "L": "LEVEL3",
                          "N": "LANAUTILUS",
                          "C": "CENTURY",
                          "T": "TELXIUS"
                          },
                    "F": {"DATA": "FIBRA_DIRECTA",
                          "0": "0-10m",
                          "1": "11-20m",
                          "2": "20-100m",
                          "3": "100-1000m",
                          "4": "1-5km",
                          "5": "6-10km",
                          "6": "10-40km",
                          "7": "40-80km",
                          "8": "80-500km",
                          "9": ">500km ",
                          },
                    "W": {"DATA": "PSEUDOWIRE",
                          "S": "SUBINTERFACE",
                          "R": "ROUTED_VPLS"}}

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        l3 = re.findall("L3:\w*", self.description)
        self.l3_protocol = "UNKNOWN"
        self.l3_protocol_attr = "UNKNOWN"
        self.direction = "UNKNOWN"
        if l3:
            print(l3[0][3:6], " ", l3[0][6:])
            if (l3[0][3:6] == "MPL"):
                self.l3_protocol = "MPLS"
            elif l3[0][3:6] == "BGP":
                self.l3_protocol = "BGP"
            self.l3_protocol_attr = l3[0][6:]
        direction = re.findall("D:\w*", self.description)
        if direction:
            try:
                self.data_flow = self.directions[direction[0].split(":")[1]]
            except KeyError:
                self.data_flow = "UNKNOWN"

        l1 = re.findall("L1:\S*", self.description)
        if l1:
            l1_info = l1[0].split(":")[0].split()
            try:
                self.l1_protocol = self.l1_converter[l1_info[0]]["DATA"]
                try:
                    self.self.l1_protocol_attr = self.l1_converter[l1_info[0]][l1_info[1]]
                except KeyError:
                    self.l1_protocol_attr = "UNKNOWN"
            except KeyError:
                self.l1_protocol = "UNKNOWN"
                self.l1_protocol_attr = "UNKNOWN"
        else:
            self.l1_protocol = "UNKNOWN"
            self.l1_protocol_attr = "UNKNOWN"

    def uid_db(self):

        try:
            connection = self.parent_device.master.db_connect()
            with connection.cursor() as cursor:
                sql = '''SELECT uid FROM interfaces WHERE if_index=%s AND net_device_iud =%s'''
                cursor.execute(sql, (self.if_index, self.parent_device.uid_db()))
                result = cursor.fetchone()
                if (result):
                    self.uid = result['uid']
                    connection.close()
                    return self.uid
                else:
                    self.uid = 0
                    connection.close()
                    return 0
        except Exception as e:
            print(e)
            connection.close()
            return 0

    def save(self):
        if self.parent_device.uid_db() == 0:
            self.parent_device.save()
        print("parent uid ", self.parent_device.uid)
        try:
            connection = self.parent_device.master.db_connect()
            with connection.cursor() as cursor:
                sql = '''INSERT INTO 
                interfaces(if_index,
                description,
                bandwith,
                l3_protocol,
                l3_protocol_attr
                ,l1_protocol,
                l1_protocol_attr,
                data_flow,
                net_device_iud)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)'''

                cursor.execute(sql, (self.if_index,
                                     self.description,
                                     self.bw,
                                     self.l3_protocol,
                                     self.l3_protocol_attr,
                                     self.l1_protocol,
                                     self.l1_protocol_attr,
                                     self.data_flow,
                                     self.parent_device.uid))
                connection.commit()
                self.uid = cursor.lastrowid
            return self.uid
        except Exception as e:
            print(e)
            return False

    def in_db(self):
        if self.uid != 0:
            return True
        elif self.get_uid_db() == 0:
            return False
        else:
            return True
