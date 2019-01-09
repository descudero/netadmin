import re
from datetime import datetime
from collections import OrderedDict


def tdm(start, end):
    return (end - start).microseconds / 1000

def normalize_interface_name(interface_string):
    '''

    :param interface_string:
    :return:
    returns the value of a string with interface normalized data.
    '''

    interface_dict = {"TenGigabitEthernet": "Te",
                      "GigabitEthernet": "Gi",
                      "TenGigE": "Te",
                      "HundredGigE": "Hu",
                      "FortyGigE": "Fo"}
    for match, replace in interface_dict.items():
        interface_string = interface_string.replace(match, replace)
    return interface_string


class performance_log():

    def __init__(self, name):
        self.name = name
        self.flags = OrderedDict()
        self.flags["start"] = datetime.now()

    def new_flag(self, flag_name):
        self.flags[flag_name] = datetime.now()

    def flag(self, flag_name):
        self.new_flag(flag_name=flag_name)

    @property
    def start(self):
        return self.flags["start"]

    @start.setter
    def start(self, value):
        self.flags["start"] = value

    @property
    def end(self):
        return self.flags.get("end", datetime.now)

    @start.setter
    def end(self, value):
        self.flags["end"] = value

    def __repr__(self):
        return "{0} ms".format(tdm(self.start, self.end))

    def print_intervals(self):
        last_key = None
        print("performance log " + self.name)
        for key, time in self.flags.items():
            if last_key is None:
                print("F:", key, tdm(time, self.end), "ms total time")
                last_key = key
            else:
                print("F:", last_key, "->", key, tdm(time, self.flags[last_key]), "ms")
                last_key = key
