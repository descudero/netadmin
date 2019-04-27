#!/bin/bash
### Do not do the following it will not work ###
#source activate AVirtualEnvironment
#python mypythonscript.pyK
#source deactivate AVirtual Environment
filename="snmp_interface_poll_ips"
while read -r line; do
    name="$line"
    cd /www/netadmin && /home/admins/ufilatam/netadmin-env/bin/python3 "/www/netadmin/save_snmp_interfaces.py" $line  &
done < "$filename"
