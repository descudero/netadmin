from tools import get_oid_size, get_bulk, logged
import datetime


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

    STATE_DICT = {1: 'idle',
                  2: 'connect',
                  3: 'active',
                  4: 'opensent',
                  5: 'openconfirm',
                  6: 'established'

                  }

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
        if self.parent.uid_db() == 0:
            self.parent.save()
        try:
            connection = self.parent.master.db_connect()
            with connection.cursor() as cursor:

                sql = f'''INSERT INTO 
                       bgp_neighbors(ip,asn,address_family,
                       net_device_uid)
                       VALUES ('{self.ip}','{self.asn}','{self.address_family}','{(self.parent.uid)}')'''

                cursor.execute(sql)
                connection.commit()
                self.uid = cursor.lastrowid
            return self.uid

        except Exception as e:
            self.db_log.warning(f"bgp_save bgp {self.ip} dev {self.parent.ip} error en bulk save {repr(e)} {sql}")
            return 0

    def uid_db(self):

        try:
            connection = self.device.master.db_connect()
            with connection.cursor() as cursor:
                sql = f'''SELECT uid FROM bgp_neighbors WHERE ip={self.ip} AND net_device_uid ={self.parent.uid} 
                '''
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
            self.db_log.warning(f"get uid bgp {self.ip} dev {self.parent.ip} error  {repr(e)} ")
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

        return {ip: BGPNeighbor(ip=ip, parent_device=device, address_family=address_family, **record) for ip, record in
                snmp_dict.items()}

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
                    ip = ip[:-4]
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
            print(sql)
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
