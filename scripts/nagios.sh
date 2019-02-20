#!/bin/bash
### Do not do the following it will not work ###
#source activate AVirtualEnvironment
#python mypythonscript.pyK
#source deactivate AVirtual Environment

### Do this instead ###
cd /www/netadmin && /home/admins/ufilatam/netadmin-env/bin/python3 "/www/netadmin/nagios.py" $0 $1 $2 $3




