import getpass;

from config.Master import Master;
from model.BaseDevice import BaseDevice;

master = Master()
ip = getpass._raw_input("ip del cisco")
EquipoPrueba = BaseDevice(ip, "pba", master)

device = EquipoPrueba.connect()
# print(EquipoPrueba.sendCommand(device,"show conf"))


print(EquipoPrueba.get_recursive_routes())
