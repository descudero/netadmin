import argparse

from model.L3Path import L3Path
from model.claseClaro import Claro

parser = argparse.ArgumentParser(description='L3 path verifier')
parser.add_argument('ip', type=str,
                    help='First L3 device')
parser.add_argument('prefix', type=str,
                    help='destination address')
parser.add_argument('-i', '--int_stats', action="store_true",
                    help='display interface stats')
parser.add_argument('-l', '--log', action="store_true",
                    help='save log')
parser.add_argument('-lf', '--log_filter',
                    help='filter for log')
args = parser.parse_args()
claro = Claro()
claro.set_master(username="", password="")
l3 = L3Path(network_model=claro, device_ip=args.ip, prefix=args.prefix, vrf="null", parent="null")
l3.search_recursive_path_route()
print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print("%%%%%%%%%%%%%%     Path L3            %%%%%%%%%%%%%%%%%")
print(l3.string_path())

if (args.log):
    print("%%%%%%%%%%%%%%%%%%% Logs %%%%%%%%%%%%%%%%%%%%%%%%%")
    l3.get_log(args.log_filter)

if (args.int_stats):
    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    print("%%%%%%%%%%%%%%%Stats Interface   %%%%%%%%%%%%%%%%%%%%%%")
    print(l3.get_interfaces_stats())
print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
print("$       Codigo creado por Daniel Escudero        $")
print("$________________________________________________$")
print("$ Si les resolvio su problema se aceptan         $")
print("$             donas como donacion                $")
print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
