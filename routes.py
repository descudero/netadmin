import re
import sys
import pexpect
from pexpect import popen_spawn
import telnetlib

HOST = '10.192.129.34'  # this is the hostname for device, to be changed
user = "descudero"
password = "zekto2014-"

tn = telnetlib.Telnet(HOST)  # make less typing for me
tn.set_debuglevel(9)
tn.read_until(str.encode('username:'))  # expected prompt after telnetting to the
tn.write(str.encode(user + '\r\n'))  # hopefully write username and pass characte
# this is where the program appears to hang
tn.read_until(str.encode('password:'))  # expected prompt after putting in the
tn.write(str.encode(password + '\r\n'))
# this should be the prompt after enable
tn.read_until(str.encode('#'))
tn.write(str.encode("show conf | i hostname\r\n"))

hostname = tn.read_until(str.encode('#')).decode().replace("\r", "").split("\n")[1].replace("hostname ", "")
tn.write(str.encode('terminal length 0\r\n'))  # run this command, read this from file
tn.read_until(str.encode(hostname + '#'))  # prompt once above command has finished
tn.write(str.encode('show run \r\n'))  # run this command, read this from file
configuration = tn.read_until(str.encode(hostname + '#'))  # prompt once above command has finished

tn.write(str.encode('exit' '\r\n'))  # disconnect from the session
# configuration=tn.read_all()  # prints out something, maybe needs to be prior to
tn.close()
configuration = configuration.decode()
# print(configuration)
url = 'C:\\Users\\descudero\\conflou.txt'
Archivo = open(url, 'r')
lineasConfig = configuration.split("\n")

routes = {};

show = ""
for index, linea in enumerate(lineasConfig):
    if (linea.startswith("ip route vrf")):
        linea = linea.replace("\n", "")
        linea_split = linea.split(" ")
        next_hop = linea_split[6]
        pat = re.compile("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}")
        test = pat.match(next_hop)
        if (test):
            pass
        else:
            next_hop = next_hop = linea_split[7]
        route = linea_split[4]
        mask = linea_split[5]
        vrf = linea_split[3]
        show += "\n" + "show ip route vrf " + vrf + " " + next_hop + " \n"
        routes[next_hop + vrf] = [vrf, route, mask, next_hop, linea]
afterShow = True

tn = telnetlib.Telnet(HOST)  # make less typing for me
# tn.set_debuglevel(9)
tn.read_until(str.encode('username:'))  # expected prompt after telnetting to the
tn.write(str.encode(user + '\r\n'))  # hopefully write username and pass characte
# this is where the program appears to hang
tn.read_until(str.encode('password:'))  # expected prompt after putting in the
tn.write(str.encode(password + '\r\n'))
# this should be the prompt after enable
tn.read_until(str.encode('#'))
tn.write(str.encode("show conf | i hostname\r\n"))

hostname = tn.read_until(str.encode('#')).decode().replace("\r", "").split("\n")[1].replace("hostname ", "")
tn.write(str.encode('terminal length 0\r\n'))  # run this command, read this from file
tn.read_until(str.encode(hostname + '#'))  # prompt once above command has finished
tn.write(str.encode(show))  # run this command, read this from file
tn.write(str.encode("error_generado"))
show_result = tn.read_until(str.encode("error_generado"))  # prompt once above command has finished
tn.write(str.encode('exit' '\r\n'))  # disconnect from the session
# configuration=tn.read_all()  # prints out something, maybe needs to be prior to
tn.close()
show_result = show_result.decode().replace("\r", "").split("\n")

# print(show_result)
if (afterShow):
    url2 = 'C:\\Users\\descudero\\showroute.txt'
    Archivo2 = open(url2, 'r')
    lineasShow = show_result
    inRoute = False;
    isDefault = True;
    rutas = []

    command = ""
    for index, linea2 in enumerate(lineasShow):

        if (linea2.find("show ip route") != -1):
            vrf = linea2.split(" ")[4]
            next_hop = linea2.split(" ")[5]

        if (linea2.find("default") != -1):
            # print(next_hop+vrf)
            ruta = (routes[next_hop + vrf])
            command += "no " + ruta[4] + "\n"
    print(command)
