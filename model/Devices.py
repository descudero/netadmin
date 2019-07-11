from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
import ipaddress
from multiping import multi_ping
import threading  as th
from tools import logged
from multiprocessing import Process
import time
from model.InterfaceUfinet import InterfaceUfinet
from collections import defaultdict


@logged
class Devices:

    def __init__(self, master, ip_list=[], network="", platfforms={}, check_up=True):
        self.errors = {}
        self.master = master
        self.devices = dict()
        self.uid_devices = {}
        if network != "" and len(ip_list) == 0:
            ip_list = [str(host) for host in ipaddress.ip_network(network).hosts()]
        for ip in ip_list:
            if not platfforms:
                self.devices[ip] = CiscoIOS(ip=ip, display_name="", master=master)
            else:
                self.devices[ip] = eval(platfforms[ip])(ip=ip, display_name="", master=master)

        if check_up:
            self.execute(methods=["check_able_connect"], thread_window=50)
            self._not_connected_devices = {ip: device for ip, device in self.devices.items() if not device.able_connect}
            self.devices = {ip: device for ip, device in self.devices.items() if device.able_connect}
            self.execute(methods=["set_snmp_community"], thread_window=50)

        if not platfforms:
            self.__correct_classes()

        self.set_uid = False

    @staticmethod
    def factory_device(master, ip):
        return list(Devices(master=master, ip_list=[ip]).devices.values())[0]

    def __len__(self):
        return len(self.devices)

    def __getitem__(self, item):
        return self.devices.__getitem__(item)

    def items(self):
        return self.devices.items()

    def values(self):
        return self.devices.values()

    def keys(self):
        return self.devices.keys()

    def __iter__(self):
        return iter(self.devices.values())

    def remove_duplicates_db(self):
        self.execute(methods=["duplicate_db"])
        self.devices = {ip: device for ip, device in self.items() if not device.duplicate}

    def __correct_classes(self):
        self.execute(methods=["get_platform"])
        new_devices = {}
        for ip, device in self.devices.items():
            platform = device.platform
            hostname = device.hostname
            community = device.community
            if device.platform != "CiscoIOS":
                device = eval(device.platform)(device.ip, device.display_name, self.master)
            new_devices[ip] = device
            device.platform = platform
            device.hostname = hostname
            device.community = community

        self.devices = new_devices

    def run_methods(self, methods, kwargs={}):

        for method in methods:

            for count, device in enumerate(self):
                self.dev.info("dev {0} execute method {1}".format(device, method))

                try:
                    getattr(device, method)()

                except Exception as e:
                    self.errors.get(device.ip, []).append(repr(e))
                    self.verbose.warning("dev {0} excute method {1} error {2}".format(device, method, repr(e)))

    def execute(self, methods, kwargs={}, thread_window=100, deferred=False, deferred_seconds=5, deferred_group=5):
        th.Thread()
        threads = []
        deferred_count = 0
        for method in methods:

            for count, device in enumerate(self):
                self.dev.info("dev {0} execute method {1}".format(device, method))

                try:

                    if len(threads) < thread_window or deferred:
                        method_instantiated = getattr(device, method)

                        if device.ip in kwargs:
                            try:

                                t = th.Thread(target=method_instantiated, kwargs=kwargs[device.ip][method],
                                              name=f'{device.ip} {method} ')
                            except KeyError as e:
                                self.dev.warning(f'execute threads error in Kwags {e} {kwargs} ')
                        else:
                            t = th.Thread(target=method_instantiated)
                        t.start()
                        threads.append(t)
                        if deferred:
                            deferred_count += 1
                            if deferred_group == deferred_count:
                                time.sleep(deferred_seconds)
                                deferred_count = 0
                    else:
                        for t in threads:
                            t.join()
                        threads = []

                        self.verbose.info(f"execute {method} devices done{count + 1} total {len(self)}")
                except Exception as e:
                    self.errors.get(device.ip, []).append(repr(e))
                    self.verbose.warning("dev {0} excute method {1} error {2}".format(device, method, repr(e)))
        for t in threads:
            t.join()

    def dict_from_sql(self, sql) -> list:
        self.db_log.warning(f'dict_from_sql {sql}')
        try:
            connection = self.master.db_connect()
            with connection.cursor() as cursor:
                cursor.execute(sql)
                data = cursor.fetchall()
                return data
        except Exception as e:
            self.db_log.warning(f'dict_from_sql error  {e} {sql}')
            return []

    def set_uids(self):
        ipdevs = [f"'{dev.ip}'" for dev in self]
        sql = f'SELECT uid,ip FROM netadmin.network_devices where ip in({",".join(ipdevs)})'
        data = self.dict_from_sql(sql=sql)
        for row in data:
            self.devices[row['ip']].uid = row['uid']
        for device in self:
            if device.uid == 0:
                device.save()
        self.set_uid = True

    def uid_dict(self):
        if not self.set_uid:
            self.set_uids()

        if len(self.uid_devices) == 0:
            self.uid_devices = {dev.uid: dev for dev in self}

    def set_interfaces_db(self):
        self.uid_dict()
        self.verbose.warning(f'set_interfaces_db INIT')
        sql = InterfaceUfinet.sql_today_last_polled_interfaces(self.values())

        data_interfaces = self.dict_from_sql(sql=sql)

        data_segmented_by_uid = defaultdict(list)
        for row in data_interfaces:
            data_segmented_by_uid[row['net_device_uid']].append(row)

        for device in self:
            device.set_interfaces_data(interfaces_data=data_segmented_by_uid[device.uid])
        self.verbose.warning(f'set_interfaces_db FINISH')

    def set_interfaces_db_period(self, period_start, period_end):
        self.uid_dict()
        sql = InterfaceUfinet.sql_last_period_polled_interfaces(devices=self.values(),
                                                                date_start=period_start,
                                                                date_end=period_end)
        data_interfaces = self.dict_from_sql(sql=sql)
        data_segmented_by_uid = defaultdict(list)
        for row in data_interfaces:
            data_segmented_by_uid[row['net_device_uid']].append(row)

        for device in self:
            device.set_interfaces_data(interfaces_data=data_segmented_by_uid[device.uid])

    def execute_processes(self, methods, kwargs={}, thread_window=100):

        processes = []
        for method in methods:

            for count, device in enumerate(self):
                self.dev.info("dev {0} excute method {1}".format(device, method))

                try:
                    if len(processes) < thread_window:
                        method_instantiated = getattr(device, method)
                        if device.ip in kwargs:
                            try:
                                p = Process(target=method_instantiated, kwargs=kwargs[device.ip][method])
                            except KeyError as e:
                                self.dev.warning(f'execute_processes error in Kwags {e} {kwargs} ')
                        else:
                            p = th.Thread(target=method_instantiated)
                        p.start()
                        processes.append(p)
                    else:
                        self.dev.info("execute_processes: Window join ")
                        self.verbose.info("execute_processes: Window join ")

                        for p in processes:
                            p.join()
                        processes = []
                        self.verbose.info(f"execute_processes {method} devices  done{count + 1} total {len(self)}")
                except Exception as e:
                    self.errors.get(device.ip, []).append(repr(e))
                    self.verbose.warning("dev {0}execute_processes {1} error {2}".format(device, method, repr(e)))
        for p in processes:
            p.join()

    @staticmethod
    def load_uids(master, uids=[]):
        connection = master.db_connect()
        with connection.cursor() as cursor:
            join_data = ",".join([f"'{uid}'" for uid in uids])
            sql = f'''SELECT * FROM    netadmin.network_devices WHERE   uid in ({join_data}) '''
            cursor.execute(sql)
            data_devices = cursor.fetchall()
            data_devices = {register["ip"]: register for register in data_devices}
            platforms = {register["ip"]: register["platform"] for register in data_devices.values()}
            devices = Devices(master=master, ip_list=data_devices.keys(), check_up=False, platfforms=platforms)
            for device in devices:
                device.uid = data_devices[device.ip]["uid"]
                device.hostname = data_devices[device.ip]["hostname"]
                device.platform = data_devices[device.ip]["platform"]
                device.country = data_devices[device.ip]["country"]
            return devices
        return None

    @staticmethod
    def load_uid(master, uid=0):
        return list(Devices.load_uids(master=master, uids=[uid]))[0]

    def copy_attr(self, other_devices, attrs=[]):
        for device in self:
            if device.ip in other_devices.devices:
                other = other_devices[device.ip]
                for attr in attrs:
                    setattr(device, attr, getattr(other, attr))


    def set_attrs(self, data):
        for device_ip, attrs in data.items():
            for attr, value in attrs.items():
                try:
                    setattr(self.devices[device_ip], attr, value)
                except:
                    self.verbose.warning(f'error {attr} {device_ip}')

    def save_interfaces(self):
        InterfaceUfinet.save_bulk_states_devices(self)
