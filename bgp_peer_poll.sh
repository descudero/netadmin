filename="/www/netadmin/bgp_pe_list"
while read -r line; do
    name="$line"
    cd /www/netadmin && timeout 6m /home/admins/ufilatam/netadmin-env/bin/python3 "/www/netadmin/save_bgp_peer_state_snmp.py" $line  &
done < "$filename"
