from datetime import datetime
from collections import OrderedDict
import logging
from pysnmp import hlapi


def get(target, oids, credentials, port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.getCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *construct_object_types(oids)
    )
    return fetch(handler, 1)[0]


def construct_object_types(list_of_oids):
    object_types = []
    for oid in list_of_oids:
        object_types.append(hlapi.ObjectType(hlapi.ObjectIdentity(oid)))
    return object_types


def fetch(handler, count):
    result = []
    for i in range(count):
        try:
            error_indication, error_status, error_index, var_binds = next(handler)
            if not error_indication and not error_status:

                for var_bind in var_binds:
                    items = [str(var_bind[0]), cast(var_bind[1])]
                result.append(items)
            else:
                raise RuntimeError('Got SNMP error: {0}'.format(error_indication))
        except StopIteration:
            break
    return result


def cast(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return float(value)
        except (ValueError, TypeError):
            try:
                return str(value)
            except (ValueError, TypeError):
                pass
    return value


def get_bulk(target, oids, credentials, count, start_from=0, port=161,
             engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    credentials = hlapi.CommunityData(credentials)
    handler = hlapi.bulkCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        start_from, count,
        *construct_object_types(oids)
    )
    return fetch(handler, count)


def get_bulk_auto(target, oids, credentials, count_oid, start_from=0, port=161,
                  engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    count = get(target, [count_oid], credentials, port, engine, context)[count_oid]
    return get_bulk(target, oids, credentials, count, start_from, port, engine, context)


def get_bulk_real_auto(target, oid, credentials, window_size=500, start_from=0, port=161,
                       engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    count = get_oid_size(target=target, oid=oid, credentials=credentials, window_size=window_size)
    return get_bulk(target, [oid], credentials, count, start_from, port, engine, context)


def get_oid_size(target, oid, credentials, window_size=500):
    data = []
    data_filtered = []
    while len(data) == len(data_filtered):
        window_size += 100
        data = get_bulk(target=target, oids=[oid], credentials=credentials, count=window_size)
        data_filtered = [registro for registro in data if oid in registro[0]]
    return len(data_filtered)

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
    class_.db_log = class_.log_db = logging.getLogger("db." + class_.__qualname__)

    return class_
