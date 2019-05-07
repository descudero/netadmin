from tools import get_oid_size, get_bulk, logged
import datetime
from pprint import pprint
import re


@logged
class BGPNeighbor:
    _sql_state_columns = ['state', 'last_error', 'advertised_prefixes', 'accepted_prefixes', 'bgp_neighbor_uid',
                          'state_timestamp']

    OIDS = {'state': '1.3.6.1.4.1.9.9.187.1.2.5.1.3',
            'asn': '1.3.6.1.4.1.9.9.187.1.2.5.1.11',
            'time_up': '1.3.6.1.4.1.9.9.187.1.2.5.1.19',
            'last_error': '1.3.6.1.4.1.9.9.187.1.2.5.1.28',
            'accepted_prefixes': '1.3.6.1.4.1.9.9.187.1.2.8.1.1',
            'advertised_prefixes': '1.3.6.1.4.1.9.9.187.1.2.8.1.6',
            }
    ADDRESS_FAMILY = {'ipv4': '.1.4', 'ipv6': '.2.6'}

    STATE_DICT = {0: 'NA',
                  1: 'idle',
                  2: 'connect',
                  3: 'active',
                  4: 'opensent',
                  5: 'openconfirm',
                  6: 'established'

                  }

    _sql_columns = ['net_device_uid', 'ip', 'asn', 'address_family', 'uid']
    _sql_table = 'bgp_neighbors'

    def __init__(self, parent_device, ip, asn, address_family, state, last_error, advertised_prefixes,
                 accepted_prefixes, **kwargs):
        self.parent = parent_device
        self.asn = asn
        self.ip = ip
        self.address_family = address_family
        self.state = BGPNeighbor.STATE_DICT.get(state, str(state))
        self.last_error = last_error
        self.advertised_prefixes = advertised_prefixes
        self.accepted_prefixes = accepted_prefixes
        self.uid = 0

    def uid_save(self):
        if not self.in_db():
            self.save()
        return self.uid

    def in_db(self):
        if self.uid != 0:
            return True
        elif self.uid_db() == 0:
            return False
        else:
            return True

    def save(self):
        print(f'device save bgp peer uid {self.parent.uid_db()}')
        if self.parent.uid_db() == 0:
            self.parent.save()
            print(f'device save bgp peer uid {self.parent.uid}')
        try:
            connection = self.parent.master.db_connect()
            with connection.cursor() as cursor:
                self.verbose.warning(f'device save bgp peer uid {self.parent.uid_db()}')
                sql = f'''INSERT INTO 
                       bgp_neighbors(ip,asn,address_family,
                       net_device_uid)
                       VALUES ('{self.ip}','{self.asn}','{self.address_family}','{(self.parent.uid_db())}')'''

                cursor.execute(sql)
                connection.commit()
                self.uid = cursor.lastrowid
            return self.uid

        except Exception as e:
            self.db_log.warning(f"bgp_save bgp {self.ip} dev {self.parent.ip} error en bulk save {repr(e)} {sql}")
            return 0

    def uid_db(self):

        try:
            connection = self.parent.master.db_connect()
            with connection.cursor() as cursor:
                sql = f'''SELECT uid FROM bgp_neighbors WHERE ip='{self.ip}' AND net_device_uid={self.parent.uid_db()} 
                '''
                print(sql)
                cursor.execute(sql)
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
            print('error')
            self.db_log.warning(f"get uid bgp {self.ip} dev {self.parent.ip} error  {repr(e)} ")
            print(e)
            self.uid = 0
            return 0

    @property
    def sql_state(self) -> str:
        if self.uid_save() == 0:
            return ""
        else:
            timestamp = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            return f"('{self.state}','{self.last_error}','{self.advertised_prefixes}'," \
                f"'{self.accepted_prefixes}','{self.uid}','{timestamp}')"

    @staticmethod
    def factory_snmp(device, community, address_family):
        snmp_dict = BGPNeighbor.bulk_load_snmp(device=device, community=community, address_family=address_family)
        bgp_dict = {}

        for ip, record in snmp_dict.items():
            try:
                bgp_dict[ip] = BGPNeighbor(parent_device=device, address_family=address_family, ip=ip, **record)
            except TypeError as e:
                pass
                device.dev.warning(f'factory_snmp unable to create BGPNeighbor record {record} {e}')

        return bgp_dict

    @staticmethod
    def bulk_load_snmp(device, community, address_family):
        add_oid = BGPNeighbor.ADDRESS_FAMILY[address_family]
        count = get_oid_size(device.ip, oid=BGPNeighbor.OIDS['state'] + add_oid,
                             window_size=50, credentials=community)
        device_data = {}
        for attr, oid in BGPNeighbor.OIDS.items():
            real_oid = oid + add_oid
            data_oid = get_bulk(target=device.ip, oids=[real_oid], credentials=community, count=count)
            for record in data_oid:
                ip = record[0].replace(real_oid + ".", "")
                if ip.count('.') > 3:
                    ip = re.findall(pattern="(((\d{1,3}\.){3}\d{1,3}))", string=ip)[0][0]
                value = record[1]
                device_data.setdefault(ip, {})[attr] = value
        return device_data

    @staticmethod
    def bulk_sql_state(neighbors) -> str:
        columns_sql = ",\n".join(BGPNeighbor._sql_state_columns)
        bgp_state_data = ",\n".join([neighbor.sql_state for neighbor in neighbors])
        return f'INSERT INTO \nbgp_neighbor_states({columns_sql}) VALUES {bgp_state_data}'

    @staticmethod
    def save_bulk_states(device, neighbors):
        if len(neighbors) > 0:
            BGPNeighbor.set_uids(device=device, neighbors=neighbors)
            sql = BGPNeighbor.bulk_sql_state(neighbors=neighbors)
            try:
                connection = device.master.db_connect()
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    connection.commit()
                    return 1
            except Exception as e:
                device.db_log.warning(f"bgp_state_save {device.ip} error en bulk save {repr(e)} {sql}")
                return 0
        else:
            return

    @staticmethod
    def bgp_peers_sql(devices=[], date_start="", date_end="", other_filters=""):
        filter_count = 0
        filter_count += 1 if not other_filters == "" else 0
        filters = f' {other_filters} '
        if devices:
            join_data = ",".join([f"'{device}'" for device in devices])
            filters += " AND " if filter_count > 0 else ""
            filters += f" nd.ip in  ({join_data})"
            filter_count += 1

        if not date_start == "":
            filters += " AND " if filter_count > 0 else ""
            filters += f"  bs.state_timestamp>='{date_start}'"

        if not date_end == "":
            filters += " AND " if filter_count > 0 else ""
            filters += f"  bs.state_timestamp<='{date_end}'"
        tables = f'{BGPNeighbor._sql_table} as bg INNER JOIN ' \
            f'bgp_neighbor_states as bs on bs.bgp_neighbor_uid=bg.uid ' \
            f'INNER JOIN  network_devices as nd on nd.uid=bg.net_device_uid ' \
            f'INNER JOIN (select max(uid) as uid ' \
            f'from bgp_neighbor_states group by bgp_neighbor_uid) ' \
            f'as bs2 on bs.uid = bs2.uid '

        columns = ",".join([f"bg.{column} as {column} "
                            for column in BGPNeighbor._sql_columns]) \
                  + ', nd.ip as net_device_ip , nd.hostname, bs.state as state, bs.accepted_prefixes as accepted_prefixes'

        if filter_count > 0:
            sql = f'SELECT {columns} FROM {tables} WHERE {filters} '
        else:
            sql = f'SELECT {columns} FROM {tables}  '
        return sql

    @staticmethod
    def bgp_peers_from_db(master, devices=[], date_start="", date_end="", other_filters=""):
        sql = BGPNeighbor.bgp_peers_sql(devices=devices, date_start=date_start, date_end=date_end,
                                        other_filters=other_filters)
        print(sql)
        try:
            connection = master.db_connect()
            with connection.cursor() as cursor:
                cursor.execute(sql)
                data_neighbors = cursor.fetchall()
                return data_neighbors
        except Exception as e:
            print(e)
            pass

    @staticmethod
    def set_uids(device, neighbors):
        if device.in_db():
            try:
                connection = device.master.db_connect()
                with connection.cursor() as cursor:
                    sql = f'''SELECT uid FROM    bgp_neighbors WHERE   net_device_uid ={device.uid} '''
                    cursor.execute(sql)
                    data_neighbors = cursor.fetchall()
                    data_neighbors = {data['ip']: data for data in data_neighbors}

                    for neighbor in neighbors:
                        if neighbor.ip in data_neighbors:
                            data_sql = data_neighbors[neighbor.ip]
                            neighbor.uid = data_sql['uid']
                        else:
                            neighbor.save()
                    return
            except Exception as e:
                device.db_log.warning(f'sql not able to get data {repr(e)}')
                return 0
        else:
            return 0

    @staticmethod
    def load_uid(isp, uid):
        connection = isp.master.db_connect()
        with connection.cursor() as cursor:
            sql = f'''SELECT * FROM    bgp_neighbors WHERE   uid ={uid} '''
            cursor.execute(sql)
            data = cursor.fetchone()
            data_object = dict()
            data_object['parent_device'] = isp.load_device_uid(uid=data['net_device_uid'])
            data_object['ip'] = data["ip"]
            data_object['asn'] = data["asn"]
            data_object['address_family'] = ["address_family"]
            data_object['state'] = 0
            data_object['last_error'] = ""
            data_object['advertised_prefixes'] = 0
            data_object['accepted_prefixes'] = 0
            bgp_neigbor = BGPNeighbor(**data_object)
            bgp_neigbor.uid = uid
            return bgp_neigbor

    def load_states(self, start_date, end_date):
        try:
            connection = self.parent.master.db_connect()
            with connection.cursor() as cursor:
                sql = f'''SELECT * FROM bgp_neighbor_states WHERE bgp_neighbor_uid={self.uid}\
                        AND state_timestamp >='{start_date}' AND state_timestamp<='{end_date}'
                    '''
                print(sql)
                cursor.execute(sql)

                data = cursor.fetchall()
                return data
        except Exception as e:
            print(e)

    @staticmethod
    def get_url(type, uid):
        return f"/reportes/{BGPNeighbor._sql_table}/{type}/{uid}"

    def __repr__(self):
        return f'<BGPPEER D:{self.parent.ip}  P:{self.ip} A:{self.asn} U:{self.uid}>'
