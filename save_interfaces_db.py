
from model.claseClaro import Claro
from config.Master import Master
from model.InternetServiceProvider import InternetServiceProvider as ISP
import argparse

parser = argparse.ArgumentParser(description='Interfaces report saver')
parser.add_argument('template', type=str,
                    help='template yml')
args = parser.parse_args()

isp = ISP()
isp.master = Master()
isp.save_interfaces_state_db(template=args.template)
