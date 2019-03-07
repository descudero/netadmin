from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
import time

ip = '172.16.30.44'
new_abr_ip = '172.16.30.251'
abr_ip = '172.16.30.44'
isp = ISP()
isp.master = Master()
suffix_path = "VPL9K_MIG"
cisco = CiscoIOS(ip=ip, display_name="", master=isp.master)
isp.excute_methods({"set_mpls_te_tunnels": {}, "set_ip_explicit_paths": {}}, devices=[cisco])

with open(f"{cisco.ip}_loose.txt", "w") as f:
    data = f'------------------\n{cisco.ip}\n'
    data += cisco.head_te_add_hop_ip_explicit_paths(hop={"next_hop": new_abr_ip, "loose": "loose"},
                                                    ip_reference_hop=abr_ip,
                                                    index_way_path="replace", index_way_tunnel="before",
                                                    suffix_path=suffix_path)

    f.write(data)
