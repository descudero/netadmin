
from model.claseClaro import Claro
from config.Master import Master
from model.CiscoXR import CiscoXR
from pprint import pprint
import argparse

parser = argparse.ArgumentParser(description='Interfaces report Generator')
parser.add_argument('network', type=str,
                    help='network wirh prefix exp 10.0.0.0/16')
parser.add_argument('filename', type=str,
                    help='file_name_full_path')
parser.add_argument('-i', '--int_stats', action="store_true",
                    help='display interface stats')

args = parser.parse_args()
claro = Claro()
claro.set_master(password=Master.decode("ufinet", "w4rDjMOSw5zDisOowqbCnsOI"),
                 username=Master.decode("pinf con vrf", "w5fDjsOhw5rCicOSw50="))
pprint(claro.generate_report_consumption(network=args.network, filename=args.filename))
