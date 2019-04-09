from model.Devices import Devices
from config.Master import Master

devices = Devices(master=Master(), network="172.16.30.0/24")

for device in devices:
    print(repr(device))
