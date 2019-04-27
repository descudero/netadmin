from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
import ipaddress
from multiping import multi_ping
import threading  as th
from tools import logged
from multiprocessing import Process

@logged
class Devices:

    def __init__(self, master, ip_list=[], network=""):
        self.errors = {}
        self.master = master
        self.devices = dict()
        if network != "" and len(ip_list) == 0:
            ip_list = [str(host) for host in ipaddress.ip_network(network).hosts()]
        for ip in ip_list:
            self.devices[ip] = CiscoIOS(ip=ip, display_name="", master=master)
        self.execute(methods=["check_able_connect"])
        self._not_connected_devices = {ip: device for ip, device in self.devices.items() if not device.able_connect}
        self.devices = {ip: device for ip, device in self.devices.items() if device.able_connect}

        self.__correct_classes()

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
            device = eval(device.platform)(device.ip, device.display_name, self.master)
            new_devices[ip] = device
            device.platform = platform
            device.hostname = hostname
            device.community = community
        self.devices = new_devices

    def execute(self, methods, kwargs={}, thread_window=100):
        th.Thread()
        threads = []
        for method in methods:

            for device in self:
                self.dev.info("dev {0} excute method {1}".format(device, method))
                self.verbose.info("dev {0} excute method {1}".format(device, method))
                try:
                    print(kwargs.keys())
                    if len(threads) < thread_window:
                        method_instantiated = getattr(device, method)
                        print(device.ip in kwargs)
                        if device.ip in kwargs:
                            try:
                                print(kwargs[device.ip][method])
                                t = th.Thread(target=method_instantiated, kwargs=kwargs[device.ip][method],
                                              name=f'{device.ip} {method} ')
                            except KeyError as e:
                                print(e)
                        else:
                            t = th.Thread(target=method_instantiated)
                        t.start()
                        threads.append(t)
                    else:
                        self.dev.info("excute_methods: Window join ")
                        self.verbose.info("excute_methods: Window join ")
                        for t in threads:
                            t.join()
                        threads = []

                except Exception as e:
                    self.errors.get(device.ip, []).append(repr(e))
                    self.verbose.warning("dev {0} excute method {1} error {2}".format(device, method, repr(e)))
        for t in threads:
            t.join()

        def execute(self, methods, kwargs={}, thread_window=100):
            th.Thread()
            threads = []
            for method in methods:

                for device in self:
                    self.dev.info("dev {0} excute method {1}".format(device, method))
                    self.verbose.info("dev {0} excute method {1}".format(device, method))
                    try:
                        print(kwargs.keys())
                        if len(threads) < thread_window:
                            method_instantiated = getattr(device, method)
                            print(device.ip in kwargs)
                            if device.ip in kwargs:
                                try:
                                    print(kwargs[device.ip][method])
                                    t = th.Thread(target=method_instantiated, kwargs=kwargs[device.ip][method],
                                                  name=f'{device.ip} {method} ')
                                except KeyError as e:
                                    print(e)
                            else:
                                t = th.Thread(target=method_instantiated)
                            t.start()
                            threads.append(t)
                        else:
                            self.dev.info("excute_methods: Window join ")
                            self.verbose.info("excute_methods: Window join ")
                            for t in threads:
                                t.join()
                            threads = []

                    except Exception as e:
                        self.errors.get(device.ip, []).append(repr(e))
                        self.verbose.warning("dev {0} excute method {1} error {2}".format(device, method, repr(e)))
            for t in threads:
                t.join()

    def execute_processes(self, methods, kwargs={}, thread_window=100):

        processes = []
        for method in methods:

            for device in self:
                self.dev.info("dev {0} excute method {1}".format(device, method))
                self.verbose.info("dev {0} excute method {1}".format(device, method))
                try:
                    print(kwargs.keys())
                    if len(processes) < thread_window:
                        method_instantiated = getattr(device, method)
                        print(device.ip in kwargs)
                        if device.ip in kwargs:
                            try:
                                print(kwargs[device.ip][method])
                                p = Process(target=method_instantiated, kwargs=kwargs[device.ip][method])
                            except KeyError as e:
                                print(e)
                        else:
                            p = th.Thread(target=method_instantiated)
                        p.start()
                        processes.append(p)
                    else:
                        self.dev.info("excute_methods: Window join ")
                        self.verbose.info("excute_methods: Window join ")
                        for p in processes:
                            p.join()
                        processes = []

                except Exception as e:
                    self.errors.get(device.ip, []).append(repr(e))
                    self.verbose.warning("dev {0} excute method {1} error {2}".format(device, method, repr(e)))
        for p in processes:
            p.join()
