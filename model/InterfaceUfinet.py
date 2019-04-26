from model.InterfaceIOS import InterfaceIOS
from collections import OrderedDict
import time
import datetime
import re
from itertools import islice
from tools import logged
import pandas as pd
import pymysql.cursors
import pymysql
from tools import get_bulk_real_auto, get_oid_size, get_bulk
from pprint import pprint
import time


@logged
class InterfaceUfinet(InterfaceIOS):
    '''
    This interface ins to accomodate the standard for clasificacion of the interface, and give some special attributtes via
    description of the interface:
    l3_rotocol
    L1_conection
    '''
    FILTERS_GROUP = {'OSPF_MPLS': {'OSPF_MPLS': {'l3p': 'MPLS', 'l3a': 'OSP'}}}

    _PROTOCOL_STATES = {1: 'up',
                        2: 'down',
                        3: 'testing',
                        4: 'unknown',
                        5: 'dormant',
                        6: 'notPresent',
                        7: 'lowerLayerDown'}

    _LINK_STATE = {1: 'up',
                   2: 'down',
                   3: 'testing'}
    _sql_state_columns = ['link_state',
                          'protocol_state',
                          'input_rate',
                          'output_rate',
                          'util_in',
                          'util_out',
                          'input_errors',
                          'output_errors',
                          'interface_uid',
                          'state_timestamp']

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
        self.if_index = InterfaceUfinet.get_normalize_interface_name(self.if_index)
        self.link_state = InterfaceUfinet._LINK_STATE[self.link_state] \
            if isinstance(self.link_state, int) else self.link_state
        self.protocol_state = InterfaceUfinet._PROTOCOL_STATES[self.protocol_state] \
            if isinstance(self.protocol_state, int) else self.protocol_state
        l3 = re.findall("L3:\w*", self.description)
        self.l3_protocol = "UNKNOWN"
        self.l3_protocol_attr = "UNKNOWN"
        self.data_flow = "UNKNOWN"
        if l3:

            if (l3[0][3:6] == "MPL"):
                self.l3_protocol = "MPLS"
            elif l3[0][3:6] == "BGP":
                self.l3_protocol = "BGP"
            self.l3_protocol_attr = l3[0][6:]
        direction = re.findall("D:\w*", self.description)
        if direction:
            try:
                self.data_flow = self.directions[direction[0].split(":")[1]]
            except KeyError as e:
                self.dev.info(self.parent_device.ip + " DF if" + self.if_index + repr(e))
                self.data_flow = "UNKNOWN"

        l1 = re.findall("L1:\S*", self.description)
        if l1:

            l1_info = l1[0].split(":")[1].split()[0]

            try:
                self.l1_protocol = self.l1_converter[l1_info[0]]["DATA"]
                try:

                    self.l1_protocol_attr = self.l1_converter[l1_info[0]][l1_info[1]]
                except (KeyError, IndexError) as e:
                    self.dev.info(self.parent_device.ip + " l1 if" + self.if_index + repr(e))
                    self.l1_protocol_attr = "UNKNOWN"
            except KeyError as e:
                self.dev.info(self.parent_device.ip + " L1 if" + self.if_index + repr(e))
                self.l1_protocol = "UNKNOWN"
                self.l1_protocol_attr = "UNKNOWN"
        else:
            self.l1_protocol = "UNKNOWN"
            self.l1_protocol_attr = "UNKNOWN"

    def __repr__(self):
        return "{if_index} I:{util_in} O:{util_out} L3:{l3}{l3a} L1:{l1}{l1a}" \
            .format(util_in=self.util_in, util_out=self.util_out, if_index=self.if_index,
                    l3=self.l3_protocol, l3a=self.l3_protocol_attr,
                    l1=self.l1_protocol, l1a=self.l1_protocol_attr)

    @staticmethod
    def interfaces_uid(device, interfaces):
        if device.in_db():
            try:
                connection = device.master.db_connect()
                with connection.cursor() as cursor:
                    sql = f'''SELECT uid,if_index,l3_protocol,l3_protocol_attr,l1_protocol,l1_protocol_attr,data_flow FROM                                    interfaces WHERE   net_device_uid ={device.uid} '''
                    cursor.execute(sql)
                    data_interfaces = cursor.fetchall()
                    data_interfaces = {data['if_index']: data for data in data_interfaces}
                    print(data_interfaces.keys())
                    for interface in interfaces:
                        if interface.if_index in data_interfaces:
                            data_sql = data_interfaces[interface.if_index]
                            if interface.l3_protocol == data_sql['l3_protocol'] and \
                                    interface.l3_protocol_attr == data_sql['l3_protocol_attr'] and \
                                    interface.l1_protocol == data_sql['l1_protocol'] and \
                                    interface.l1_protocol_attr == data_sql['l1_protocol_attr'] and \
                                    interface.data_flow == data_sql['data_flow']:
                                interface.uid = data_sql['uid']
                    return 1
            except Exception as e:
                device.db_log.warning(f'sql not able to get data {repr(e)}')
                return 0
        else:
            return 0

    @staticmethod
    def save_bulk_states(device, interfaces):
        if len(interfaces) > 0:
            InterfaceUfinet.interfaces_uid(device=device, interfaces=interfaces)
            sql = InterfaceUfinet.bulk_sql_state(interfaces=interfaces)
            try:
                connection = device.master.db_connect()
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    connection.commit()
                    return 1
            except Exception as e:
                device.db_log.warning(f"{device.ip} error en bulk save {repr(e)} {sql}")
                return 0
        else:
            return 0

    @staticmethod
    def bulk_sql_state(interfaces) -> str:
        columns_sql = ",\n".join(InterfaceUfinet._sql_state_columns)
        interfaces_data = ",\n".join([interface.sql_state for interface in interfaces])
        return f'INSERT INTO \ninterface_states({columns_sql}) VALUES {interfaces_data}'

    @property
    def sql_state(self) -> str:
        if self.uid_save() == 0:
            return ""
        else:
            timestamp = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            return f"('{self.link_state}','{self.protocol_state}','{self.input_rate}'," \
                f"'{self.output_rate}','{self.util_in}','{self.util_out}'," \
                f"'{self.input_errors}','{self.output_errors}','{self.uid}','{timestamp}')"

    def uid_save(self):
        if not self.in_db():
            self.save()
        return self.uid

    def uid_db(self):

        try:
            connection = self.parent_device.master.db_connect()
            with connection.cursor() as cursor:
                sql = '''SELECT uid FROM interfaces WHERE if_index=%s AND net_device_uid =%s AND l3_protocol=%s
                 AND l3_protocol_attr=%s AND l1_protocol=%s AND l1_protocol_attr=%s AND data_flow=%s
                '''
                cursor.execute(sql, (self.if_index, self.parent_device.uid_db(), self.l3_protocol,
                                     self.l3_protocol_attr, self.l1_protocol, self.l1_protocol_attr, self.data_flow))
                result = cursor.fetchone()
                if result:
                    self.uid = result['uid']
                    connection.close()
                    return self.uid
                else:
                    self.uid = 0
                    connection.close()
                    return 0
        except Exception as e:
            self.db_log.warning(self.parent_device.ip + " db" + self.if_index + repr(e))
            return 0

    def save(self):
        if self.parent_device.uid_db() == 0:
            self.parent_device.save()
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
                net_device_uid)
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
        elif self.uid_db() == 0:
            return False
        else:
            return True

    def save_state(self):
        if not self.in_db():
            self.save()
        try:
            connection = self.parent_device.master.db_connect()
            with connection.cursor() as cursor:
                timestamp = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                sql = '''INSERT INTO 
                interface_states(link_state,
                protocol_state,
                input_rate,
                output_rate,
                util_in ,
                util_out ,
                input_errors ,
                output_errors ,
                interface_uid ,
                state_timestamp)
                VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}','{9}')'''.format(self.link_state,
                                                                                               self.protocol_state,
                                                                                               self.input_rate,
                                                                                               self.output_rate,
                                                                                               self.util_in,
                                                                                               self.util_out,
                                                                                               self.input_errors,
                                                                                               self.output_errors,
                                                                                               self.uid,
                                                                                               timestamp)

                cursor.execute(sql)
                connection.commit()
            self.db_log.info(f'{self.parent_device.ip} saved interface_state {self.uid}')
            return self.uid
        except Exception as e:
            connection.rollback()
            self.db_log.warning(self.parent_device.ip + " db" + self.if_index + repr(e))
            return False

    @staticmethod
    def interface_states_data_by_date(master, initial_date, end_date, filter_keys):
        sql = '''select  
               d.hostname as host,
               i.uid,
               i.if_index as inter,
               right(i.description,CHAR_LENGTH(i.description)-20) as description,i.l3_protocol as l3p,
               i.l3_protocol_attr as l3a ,
               i.l1_protocol ,
               i.l1_protocol_attr,
               i.data_flow,
               s.util_in as util_in,util_out as util_out,
               (s.input_rate/1000000000) as in_gbs ,
               (s.output_rate/1000000000) as out_gbs
               ,s.state_timestamp  
               from network_devices as d
               inner join interfaces as i on d.uid = i.net_device_uid 
               inner join interface_states as s on i.uid = interface_uid 
               where s.state_timestamp >='{initial_date}' and s.state_timestamp <'{end_date}'
               '''.format(initial_date=initial_date, end_date=end_date)

        df = pd.read_sql(sql, con=master.db_connect())

        df2 = df[['host', 'uid', 'inter', 'description', 'l3p', 'l3a', 'l1_protocol', 'data_flow',
                  'l1_protocol_attr']].drop_duplicates(subset='uid', keep='first')
        df_proceded = (
            df.groupby(by=['uid'])['util_out', 'util_in', 'out_gbs', 'in_gbs'].quantile(.95)).round(
            1).reset_index()

        df_merge = pd.merge(df_proceded, df2, on=['uid'], how='left').sort_values(ascending=False, by=['util_out'])
        df_merge.drop(['uid'], axis=1, inplace=True)
        columns = ['host', 'inter', 'description', 'l1_protocol', 'l1_protocol_attr', 'util_in', 'util_out', 'in_gbs',
                   'out_gbs']

        sort_columns = {'default': 'util_out'}
        tables = filter_summary(df_merge, columns, sort_column=sort_columns, filter_keys=filter_keys)

        return tables

    _OID_IP = '1.3.6.1.2.1.4.20.1.2'

    _OID_RATES = {'input_rate': '1.3.6.1.2.1.31.1.1.1.6',
                  'output_rate': '1.3.6.1.2.1.31.1.1.1.10'}

    _OID = {'description': "1.3.6.1.2.1.31.1.1.1.18",

            'if_index': '1.3.6.1.2.1.2.2.1.2',
            'mtu': '1.3.6.1.2.1.2.2.1.4',
            'bw': '1.3.6.1.2.1.31.1.1.1.15',
            'link_state': '1.3.6.1.2.1.2.2.1.7',
            'protocol_state': '1.3.6.1.2.1.2.2.1.8',
            'output_errors': '1.3.6.1.2.1.2.2.1.20',
            'input_errors': '1.3.6.1.2.1.2.2.1.14'}

    @staticmethod
    def factory_from_dict(device, interfaces_data=[]) -> dict:
        interfaces_dict = {}
        for parse_data in interfaces_data:
            interface_object = InterfaceUfinet(parent_device=device, parse_data=parse_data)
            interfaces_dict[interface_object.if_index] = interface_object
        return interfaces_dict

    @staticmethod
    def bulk_snmp_data_interfaces(device) -> dict:
        count_interfaces = get_oid_size(target=device.ip, credentials=device.community, oid='1.3.6.1.2.1.31.1.1.1.18')
        interface_data = {}
        for attr, oid in InterfaceUfinet._OID.items():
            oid_data = get_bulk(target=device.ip, credentials=device.community, oids=[oid], count=count_interfaces)
            # if attr == 'bw':
            #    print(oid_data)
            for register in oid_data:
                snmp_ip = register[0].replace(oid + ".", "")
                value = register[1] * 1000000 if attr == 'bw' else register[1]
                interface_data.setdefault(snmp_ip, {})[attr] = value
        oid_data = get_bulk_real_auto(target=device.ip, credentials=device.community, oid=InterfaceUfinet._OID_IP,
                                      window_size=500)
        for register in oid_data:
            snmp_ip = str(register[1])
            ip = register[0].replace(InterfaceUfinet._OID_IP + ".", "")
            interface_data.setdefault(snmp_ip, {})['ip'] = ip
        for attr, oid in InterfaceUfinet._OID_RATES.items():
            oid_data = InterfaceUfinet.delta_oid(device=device, count=count_interfaces, oid=oid)
            for register in oid_data:
                snmp_ip = register[0].replace(oid + ".", "")
                interface_data.setdefault(snmp_ip, {})[attr] = register[1]

        return interface_data

    @staticmethod
    def delta_oid(device, count, oid, multiplier=8, sleep_time=20):
        time1 = time.time()
        data_before = get_bulk(target=device.ip, credentials=device.community, oids=[oid], count=count)
        time.sleep(sleep_time)
        time_lapse = time.time() - time1
        data_after = get_bulk(target=device.ip, credentials=device.community, oids=[oid], count=count)
        final_data = [[register[0], int(calculate_delta(new_counter=register[1],
                                                        old_counter=data_before[index][1],
                                                        timelapse=time_lapse)) * multiplier]
                      for index, register in enumerate(data_after)]
        return final_data

        pass


def calculate_delta(old_counter, new_counter, timelapse):
    new_counter = new_counter if new_counter >= old_counter else new_counter + 18446744073709551616
    return (new_counter - old_counter) / timelapse


def filter_summary(sql_dataframe, columns, sort_column={}, filter_keys={}):
    results = {}
    for key, filters in filter_keys.items():
        results[key] = sql_dataframe.copy()
        for column, value in filters.items():
            df = results[key]
            df = df[df[column] == value]
            results[key] = df
        if (key in sort_column):
            results[key] = results[key].sort_values(by=sort_column[key], ascending=False)
        elif ('default' in sort_column):
            results[key] = results[key].sort_values(by=sort_column['default'], ascending=False)

        results[key] = results[key][columns].to_dict(orient='records')
    return results
