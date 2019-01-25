import pandas as pd
from model.InternetServiceProvider import InternetServiceProvider
from config.Master import Master

df = pd.read_excel('snmp_location.xls')

print(list(df['ip']))
dict_data = dict(zip(list(df['ip']), list(df['snmp_location'])))
dict_data = {ip: {"text": location} for ip, location in dict_data.items()}

print(dict_data)
isp = InternetServiceProvider()
isp.master = Master(username="descuderor", password="zekto2014-")
devices = isp.correct_device_platform(isp.devices_from_ip_list(dict_data.keys()))
isp.excute_methods(devices=devices, methods={"configure_snmp_location": {}}, dict_kwargs=dict_data, thread_window=5)
