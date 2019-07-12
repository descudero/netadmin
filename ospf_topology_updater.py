from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.ospf_database import ospf_database

isp = ISP()
isp.master = Master()
data_networks = {'regional': {
    "ip_seed_router": "172.16.30.5", "process_id": '1', "area": '0',
    'network_name': '_ospf_ufinet_regional'
}, 'guatemala': {
    "ip_seed_router": "172.17.22.52",
    "process_id": '502', "area": '502008', 'network_name': 'RCE_GUATEMALA'
}
}

devices_ips = []
for name, kwargs_network in data_networks.items():
    dbd = ospf_database(isp=isp, source='real_time', **kwargs_network)
    dbd.save_state()
    devices_ips.extend(list(dbd.devices.devices.keys()))
devices_ips = list({ip for ip in devices_ips})
with open('hosts/interfaces/all_network_ospf_devices', 'w') as f:
    devices_ips.append('\n\n\n')
    f.write("\n".join(devices_ips))
