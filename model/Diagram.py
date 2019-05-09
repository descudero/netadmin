from tools import logged


@logged
class Diagram:

    def __init__(self, master, name):
        self.master = master
        self.name = name
        self.uid = self.uid_db()
        self.devices_uid = {}
        self.load_devices_uid_from_db()
        pass

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
                sql = f""" INSERT INTO diagram_network_devices( net_device_uid, x, y,diagram_uid) VALUES {','.join(
                    data)}"""

                cursor.execute(sql)
                connection.commit()
        except Exception as e:
            self.log_db.warning(f'load_devices_uid_from_db  DIAG {self.name} {e} ')

    def load_devices_uid_from_db(self):
        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                sql = f'''SELECT uid,net_device_uid,x,y FROM diagram_network_devices WHERE diagram_uid={self.uid} ORDER BY uid;'''
                cursor.execute(sql)
                data_sql = cursor.fetchall();
                self.devices_uid = {
                reg['net_device_uid']: {'x': float(reg['x']), 'y': float(reg['y']), 'uid': reg['uid']} for reg in
                data_sql}
        except Exception as e:
            self.log_db.warning(f'load_devices_uid_from_db  DIAG {self.name} {e} {sql}')
