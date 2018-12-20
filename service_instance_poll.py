from model.claseClaro import Claro
from config.Master import Master
from pprint import pprint
import argparse

parser = argparse.ArgumentParser(description='Services Instance report Generator')

parser.add_argument('filename', type=str,
                    help='file_name_full_path')
parser.add_argument('devices_ip', metavar='I', type=str, nargs='+',
                    help='list of ips of devices')
args = parser.parse_args()
claro = Claro()
claro.set_master(password=Master.decode("ufinet", "w4rDjMOSw5zDisOowqbCnsOI"),
                 username=Master.decode("pinf con vrf", "w5fDjsOhw5rCicOSw50="))

claro.save_to_excel_list(list_data=claro.get_service_instance_with_pseudowires(
    claro.devices_from_ip_list(args.devices_ip)), file_name=args.filename)
