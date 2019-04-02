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

data2 = isp.replace_loose_mpls_te_paths(abr_ip=abr_ip, new_abr_ip=new_abr_ip, devices=["172.16.30.44", "172.16.30.45"],
                                        suffix_path=suffix_path)

with open(f"{cisco.ip}_loose.txt", "w") as f:
    data = f'------------------\n{cisco.ip}\n'
    data += data2
    f.write(data)
