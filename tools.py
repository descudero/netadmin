import re


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
