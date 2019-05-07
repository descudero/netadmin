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