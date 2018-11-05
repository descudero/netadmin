from time import gmtime, strftime

from model.claseClaro import Claro;

claro = Claro()

claro.set_master("descudero", "zekto2014-")
claro.init_ipp()
firttime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
# 1wclaro.list_ipp["10.192.0.146"].set_interfaces_stats()
print(claro.list_ipp["10.192.0.146"].get_summarize_rate())
print(firttime)
print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
