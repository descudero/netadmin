from os import listdir
from model.claseClaro import Claro
from os.path import isfile, join
import time


class InternetServiceProvider(Claro):

    @staticmethod
    def search_file_name(folder, match):
        files = [file for file in listdir(folder) if match in file]

        return files

    def ospf_topology_dict_vs_date(self, name="ospf_ufinet_regional", date_string=time.strftime("%Y%m%d")):
        date_string = date_string.replace("-", "")
        files = InternetServiceProvider.search_file_name("shelves", date_string)
        if files:
            result = super().ospf_topology_vs(ip_seed_router="172.16.30.5",
                                              shelve_name="shelves/" + date_string + "_" + name, from_shelve=True)
        else:
            result = super().ospf_topology_vs(ip_seed_router="172.16.30.5",
                                              shelve_name="shelves/" + date_string + "_" + name,
                                              from_shelve=False)

        return result
