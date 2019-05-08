from pprint import pprint
from pysnmp import hlapi
from tools import get_bulk_real_auto, get_oid_size
from model.InternetServiceProvider import InternetServiceProvider as ISP
from config.Master import Master
from model.CiscoIOS import CiscoIOS
from model.CiscoXR import CiscoXR
import ipaddress
from model.BGPNeigbor import BGPNeighbor
import time
from model.InterfaceUfinet import InterfaceUfinet
from model.Devices import Devices
from collections import defaultdict

master = Master()
connection = master.db_connect()
with connection.cursor() as cursor:
    sql_uids = f'select uid from interfaces where uid not in(select interface_uid from interface_states group by interface_uid having count(interface_uid)>1 );'
    cursor.execute(sql_uids)

    uid_interfaces = cursor.fetchall()
    sql_update = []
    for register in uid_interfaces:
        sql_update.append(f' delete from netadmin.interfaces where uid={register["uid"]};')

    with open('fix_sql.sql', 'w') as f:
        for line in sql_update:
            f.write(line + "\n")
