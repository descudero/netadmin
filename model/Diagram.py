from tools import logged
import datetime
from model.ospf_adjacency import ospf_adjacency

from model.Devices import Devices


@logged
class Diagram:
    __table__ = "diagrams"
    def __init__(self, master, name):
        self.master = master
        self.name = name
        self.uid = self.uid_db()
        self.devices_uid = {}
        self.load_devices_uid_from_db()
        pass

    def save(self):

        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                sql = f'''INSERT INTO {Diagram.__table__}(name,description)
                  VALUES('{self.name}','{""}')'''
                cursor.execute(sql)
                connection.commit()
                self.uid = cursor.lastrowid
                connection.close()
            return self.uid
        except Exception as e:
            self.db_log.warning(f'SAVE_state {self.name} {sql} {e}')
            connection.close()
            return False



    def save_state(self, devices, adjacencies):
        self.state = DiagramState()
        self.state.diagram = self
        self.state.save()
        self.state.save_devices(devices=devices)
        self.state.save_adjacencies(adjacencies=adjacencies)


    def get_newer_state(self):
        print(f'get_newer_state u:{self.uid}')
        if self.in_db():
            try:
                connection = self.master.db_connect()
                with connection.cursor() as cursor:
                    sql = f"""SELECT uid,state_timestamp FROM diagram_states WHERE diagram_uid={self.uid} ORDER BY uid DESC limit 1"""
                    cursor.execute(sql)
                    result = cursor.fetchone()
                    self.state = DiagramState()
                    self.state.uid = result['uid']
                    self.state.state_timestamp = result['state_timestamp']
                    self.state.diagram = self
            except Exception as e:
                self.log_db.warning(f'UNABLE TO LOAD newer state {self.name} {e} {sql}')

    def uid_db(self):
        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                sql = f"""SELECT uid FROM diagrams WHERE name LIKE'{self.name}' ORDER BY uid DESC limit 1"""
                cursor.execute(sql)
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
            self.log_db.warning(f'UNABLE TO LOAD DIAG {self.name} {e} {sql}')

            return 0

    def in_db(self):
        if self.uid != 0:
            return True
        elif self.uid_db() == 0:
            return False
        else:
            return True

    def save_xy(self, data_devices):
        self.add_devices_db(data_devices=data_devices)
        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                for uid, device in data_devices.items():
                    x = device['x']
                    y = device['y']
                    if int(uid) in self.devices_uid:
                        data_before = self.devices_uid[int(uid)]
                        if data_before['x'] != x or data_before['y'] != y:
                            sql = f'''UPDATE diagram_network_devices SET x={x},y={y} WHERE uid={data_before['uid']}'''
                            print(sql)
                            cursor.execute(sql)
                connection.commit()
        except Exception as e:
            self.log_db.warning(f'save_xy  DIAG {self.name} {e} {sql}')

    def add_devices_db(self, data_devices):
        data = [f'({reg["net_device_uid"]},{reg["x"]},{reg["y"]},{self.uid})' for reg in data_devices.values()
                if int(reg["net_device_uid"]) not in self.devices_uid]
        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                sql = f""" INSERT INTO diagram_network_devices( net_device_uid, x, y,diagram_uid) 
                VALUES {','.join(data)}"""

                cursor.execute(sql)
                connection.commit()
        except Exception as e:
            self.log_db.warning(f'load_devices_uid_from_db  DIAG {self.name} {e} ')

    def load_devices_uid_from_db(self):
        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                sql = f'''SELECT uid,net_device_uid,x,y FROM diagram_network_devices WHERE diagram_uid={self.uid}
                 ORDER BY uid;'''
                cursor.execute(sql)
                data_sql = cursor.fetchall();
                self.devices_uid = {
                    reg['net_device_uid']: {'x': float(reg['x']), 'y': float(reg['y']), 'uid': reg['uid']} for reg in
                    data_sql}
        except Exception as e:
            self.log_db.warning(f'load_devices_uid_from_db  DIAG {self.name} {e} {sql}')


@logged
class DiagramState:
    __table__ = 'diagram_states'
    __columns__ = ['diagram_uid', 'state_timestamp']

    def __init__(self):
        self.uid = 0
        self.diagram = None
        self.state_timestamp = None
        self.devices_uid = {}


    @property
    def sql_values(self):
        values = [self.diagram.uid, str(self.state_timestamp)]
        return "(" + (",".join([f"'{column}'" for column in values])) + ")"

    @property
    def sql_colums(self):

        return f'({",".join(DiagramState.__columns__)})'

    @property
    def master(self):
        return self.diagram.master

    def save(self):
        self.state_timestamp = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                sql = f'''INSERT INTO {DiagramState.__table__}{self.sql_colums}
                VALUES{self.sql_values}'''
                cursor.execute(sql)
                connection.commit()
                self.uid = cursor.lastrowid
                connection.close()
            return self.uid
        except Exception as e:
            self.db_log.warning(f'SAVE_state {self.diagram.name} {sql} {e}')
            connection.close()
            return False

    def update_xy(self):
        pass

    def save_adjacencies(self, adjacencies):
        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                self.verbose.warning(f'save_adjacencies {self.diagram.name} p2p {len(adjacencies)} ')
                sql = f'''INSERT INTO diagram_state_adjacencies{ospf_adjacency.sql_columns()} VALUES'''
                data_values = []
                for adjacency in adjacencies.values():
                    adjacency.diagram_state = self
                    values = adjacency.sql_values
                    if values != "":
                        data_values.append(values)

                sql += ",".join(data_values)

                cursor.execute(sql)
                connection.commit()
                connection.close()

        except Exception as e:
            self.db_log.warning(f'save_adjacencies {self.diagram.name}  {sql} {e}')
            connection.close()
            return False

    def save_position(self, data_devices):

        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                for uid, device in data_devices.items():
                    x = device['x']
                    y = device['y']
                    self.verbose.debug(f'save_position u:{uid} x:{x} y:{y}')
                    device_before = self.devices_uid[int(uid)]
                    if device_before.x != x or device_before.y != y:
                        sql = f'''UPDATE diagram_state_net_devices SET x={x},y={y} WHERE net_device_uid={uid} AND \
                                  diagram_state_uid={self.uid}'''
                        self.verbose.warning(f'save positition {uid} {self.uid}')
                        try:
                            cursor.execute(sql)
                        except Exception as e:
                            self.db_log.warning(f'save_position cursor_excecute {self.diagram.state} {e} {sql}')
                connection.commit()
                connection.close()
        except Exception as e:
            self.verbose.warning(f'save_position  DIAG {self.diagram.state} {e} ')
            connection.close()

    def save_devices(self, devices):
        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                sql = f'''INSERT INTO diagram_state_net_devices(diagram_state_uid, net_device_uid, x, y) values '''
                data_dev = [[self.uid, device.uid, device.x, device.y] for device in devices if device.uid != 0]
                str_sql_values = []
                for row in data_dev:
                    str_sql_values.append('(' + ",".join([f"'{value}'" for value in row]) + ')')
                sql += ",".join(str_sql_values)
                cursor.execute(sql)
                connection.commit()
                connection.close()

        except Exception as e:
            self.db_log.warning(f'save_devices {self.diagram.name} {sql} {e}')
            connection.close()
            return False

    def p2p(self):
        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                sql = f'''SELECT * FROM  diagram_state_adjacencies where diagram_state_uid={self.uid}'''
                cursor.execute(sql)
                data = cursor.fetchall()
                p2p = {}
                connection.close()
                for row in data:
                    p2p[row['network_id']] = [{'router_id': row['net_device_1_ip'],
                                               'neighbor_ip': row['net_device_2_ip'],
                                               'interface_ip': row['interface_1_ip'],
                                               'metric': row['interface_1_weight'],
                                               'network': row['network_id'] + "/32"

                                               }, {'router_id': row['net_device_2_ip'],
                                                   'neighbor_ip': row['net_device_1_ip'],
                                                   'interface_ip': row['interface_2_ip'],
                                                   'metric': row['interface_2_weight'],
                                                   'network': row['network_id'] + "/32"

                                                   }]

                return p2p
        except Exception as e:
            self.db_log.warning(f'p2p error loading')
            return {}

        except Exception as e:
            self.db_log.warning(f'devices unable to load {self.diagram.name} {sql} {e}')
            connection.close()
            return {}

    def devices(self):
        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                sql = f'''SELECT nd.roll,nd.country,nd.area,nd.uid,nd.ip,nd.hostname,nd.platform,ds.x,ds.y FROM network_devices as nd inner join\
                diagram_state_net_devices as ds ON nd.uid=ds.net_device_uid where ds.diagram_state_uid={self.uid}'''
                cursor.execute(sql)
                data = cursor.fetchall()
                attrs = {row['ip']: row for row in data}
                platforms = {row['ip']: row['platform'] for row in data}

                devices = Devices(ip_list=attrs.keys(), platfforms=platforms, check_up=False, master=self.master)
                devices.set_attrs(data=attrs)
                devices.set_uid = True
                self.devices_uid = {device.uid: device for device in devices}
                connection.close()
                return devices
        except Exception as e:
            self.db_log.warning(f'devices unable to load {self.diagram.name} {sql} {e}')
            connection.close()
            return []
        return []
