
from model.claseClaro import Claro
from config.Master import Master
import argparse

parser = argparse.ArguKmentParser(description='Interfaces report saver')
parser.add_argument('template', type=str,
                    help='template yml')
args = parser.parse_args()

claro = Claro()
claro.set_master(password=Master.decode("ufinet", "w4rDjMOSw5zDisOowqbCnsOI"),
                 username=Master.decode("pinf con vrf", "w5fDjsOhw5rCicOSw50="))
claro.save_interfaces_state_db(template=args.template)
