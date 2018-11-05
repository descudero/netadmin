import getpass;

from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR

master = Master()
ip = getpass._raw_input("ip del cisco")
device_type = getpass._raw_input("ios o xr")
# EquipoPrueba = CiscoIOS(ip,"pba",master)


# device= EquipoPrueba.connect()
# print(EquipoPrueba.sendCommand(device,"show conf"))


# print(EquipoPrueba.getRecursiveRoutes())
if (device_type == "xr"):
    Equipo2 = CiscoXR(ip, "test", master)
else:
    Equipo2 = CiscoIOS(ip, "test", master)
print(Equipo2.get_recursive_routes())

getpass._raw_input(prompt=' presionar para terminar  ')
