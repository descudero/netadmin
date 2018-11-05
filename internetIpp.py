from model.claseClaro import Claro

claro = Claro()
claro.set_master(password="zekto2014-", username="descudero")
claro.init_ipp()
dict = claro.dict_qos_ipp()

csv = "ipp\tinterfaz\tpais\tsentido\trate\n"
for name_ipp, ipp in dict.items():
    for name_interfaz, interfaz in ipp.items():
        for name_direction, direction in interfaz.items():
            for name_qos, qos in direction.items():
                csv += name_ipp + "\t" + name_interfaz + "\t" + name_direction + "\t" + name_qos + "\t" + str(
                    qos["transmited"]) + "\n"

print(csv)

print(dict)
