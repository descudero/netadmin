from model.claseClaro import Claro
from model.CiscoIOS import CiscoIOS

file = open("area0paraguay.txt")
show_output = file.read()

claro = Claro()
# claro.generate_yed_ospf_area(show_output,file_name="paraguay")
