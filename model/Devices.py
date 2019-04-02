from model.CiscoIOS import CiscoIOS
import threading  as th
from tools import logged


@logged
class Devices:
    def __init__(self, master, ip_list=[]):
        self.errors = {}
        self.master = master
        self.devices = dict()
        for ip in ip_list:
            self.devices[ip] = CiscoIOS(ip=ip, display_name="", master=master)
        self.execute(methods="check_able_connect")
        self._not_connected_devices = {ip: device for ip, device in self.devices.items() if not device.able_connect}
        self.devices = {ip: device for ip, device in self.devices.items() if device.able_connect}

        self.__correct_classes()

    def __correct_classes(self):
        self.execute(methods=["get_platform"])
        new_devices = {}
        for ip, device in self.devices.items():
            platform = device.platform
            hostname = device.hostname
            device = eval(device.platform)(device.ip, device.display_name, self.master)
            new_devices[ip] = device
            device.platform = platform
            device.hostname = hostname
        self.devices = new_devices

    def execute(self, methods, kwargs={}, thread_window=100):
        th.Thread()
        threads = []
        for method in methods:

            for device in self.devices:
                self.dev.info("dev {0} excute method {1}".format(device, method))
                self.verbose.info("dev {0} excute method {1}".format(device, method))
                try:
                    if len(threads) < thread_window:
                        method_instantiated = getattr(device, method)
                        if device.ip in kwargs:
                            t = th.Thread(target=method_instantiated, kwargs=kwargs[device.ip])
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
                    self.errors.get(device.ip, default=[]).append(repr(e))
                    self.verbose.warning("dev {0} excute method {1} error {2}".format(device, method, repr(e)))
        for t in threads:
            t.join()
