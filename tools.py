from datetime import datetime
from collections import OrderedDict
import logging
import sys


def tdm(start, end):
    '''

    :param start:
    :param end:
    :return:
    time in miliseconds
    '''
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


def replace(string_input, matches, replace_string=""):
    for match in matches:
        string_input = string_input.replace(match, replace_string)
    return string_input


class PerformanceLog():
    '''
    class for performance log
    '''

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

    def time_flag(self, end_flag="end", start_flag="start"):
        return tdm(end=self.flags[end_flag], start=self.flags[start_flag])

    def format_time_lapse(self, end_flag="end", start_flag="start"):
        return self.name + " FROM: {0} {1} TO {2} {3} TIME LAPSED #{4}".format(start_flag,
                                                                               self.flags[start_flag],
                                                                               end_flag,
                                                                               self.flags[end_flag],
                                                                               self.time_flag(end_flag=end_flag,
                                                                                              start_flag=start_flag))


def logged(class_):
    '''
    :param class_:
    class decorator for logs
    '''
    class_.verbose = logging.getLogger("verbose." + class_.__qualname__)
    class_.logger_audit = logging.getLogger("audit." + class_.__qualname__)
    class_.logger_connection = logging.getLogger("connection." + class_.__qualname__)
    class_.dev = logging.getLogger("dev." + class_.__qualname__)
    class_.per = logging.getLogger("per." + class_.__qualname__)
    class_.db_lo = class_.log_db = logging.getLogger("db." + class_.__qualname__)

    return class_
