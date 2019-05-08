SELECT i.uid,count(s.uid) as uids
from interfaces as i
       inner join interface_states as s on s.interface_uid = i.uid
where i.net_device_uid = 1
group by i.uid
having count(s.uid) > 0;