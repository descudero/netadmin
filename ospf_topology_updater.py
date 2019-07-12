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

for name, kwargs_network in data_networks.items():
    dbd = ospf_database(isp=isp, source='real_time', **kwargs_network)
    dbd.save_state()
