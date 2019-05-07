select *
from bgp_neighbors


select *
from network_devices


SELECT bg.net_device_uid as net_device_uid,
       bg.ip             as ip,
       bg.asn            as asn,
       bg.address_family as address_family,
       bg.uid            as uid,
       nd.ip             as net_device_ip,
       nd.hostname,
       bs.state          as state
FROM bgp_neighbors as bg
       INNER JOIN bgp_neighbor_states as bs on bs.bgp_neighbor_uid = bg.uid
       INNER JOIN network_devices as nd on nd.uid = bg.net_device_uid
       INNER JOIN (select max(uid) as uid from bgp_neighbor_states group by bgp_neighbor_uid) as bs2 on bs.uid = bs2.uid
WHERE bs.state LIKE 'established'
  AND bs.state_timestamp >= '2019-05-07 00:00:00'
  AND bs.state_timestamp <= '2019-05-07 23:59:00'
SELECT *
FROM bgp_neighbor_states
WHERE bgp_neighbor_uid = 26588
  AND state_timestamp >= '2019-05-07 00:00:00'
  AND state_timestamp <= '2019-05-07 23:59:00'


select *
from interface_states
where link_state not like 'up'
order by uid DESC
limit 10;


SELECT i.uid      as uid,
       i.if_index as if_index,
       i.l3_protocol,
       i.l3_protocol_attr,
       i.l1_protocol,
       i.l1_protocol_attr,
       i.data_flow,
       s.util_in  as util_in,
       s.util_out as util_out,
       s.link_state,
       s.protocol_state,
       s.output_rate,
       s.input_rate,
       s.state_timestamp

from network_devices as d
       inner join interfaces as i on d.uid = i.net_device_uid
       inner join (select * from interface_states where DATE(state_timestamp) = DATE(NOW())) as s
                  on s.interface_uid = i.uid
       inner join (select max(uid) as uid from interface_states group by interface_uid) as s2 on s2.uid = s.uid
WHERE net_device_uid = 1
  and state_timestamp >= '2019-05-07 00:00:00'
  and state_timestamp <= '2019-05-07 23:59:00'

SELECT i.uid      as uid,
       i.if_index as if_index,
       i.l3_protocol,
       i.l3_protocol_attr,
       i.l1_protocol,
       i.l1_protocol_attr,
       i.data_flow,
       s.util_in  as util_in,
       s.util_out as util_out,
       s.link_state,
       s.protocol_state,
       s.output_rate,
       s.input_rate,
       s.state_timestamp

from network_devices as d
       inner join interfaces as i on d.uid = i.net_device_uid
       inner join (select * from interface_states where DATE(state_timestamp) = DATE(NOW())) as s
                  on s.interface_uid = i.uid
       inner join (select max(uid) as uid from interface_states group by interface_uid) as s2 on s2.uid = s.uid
WHERE net_device_uid = 3
  and state_timestamp >= '2019-05-07 00:00:00'
  and state_timestamp <= '2019-05-07 23:59:00'
select *
from interfaces


ALTER TABLE interfaces
  ADD COLUMN ip VARCHAR(70) AFTER if_index;