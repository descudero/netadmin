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

select count(uid)
from network_devices;

select *
from network_devices
where ip = '172.16.30.43'
select *
from interfaces
where net_device_uid = 55;
INSERT INTO interfaces(if_index,
                       description,
                       bandwith,
                       l3_protocol,
                       l3_protocol_attr
  , l1_protocol,
                       l1_protocol_attr,
                       data_flow,
                       net_device_uid, ip)
VALUES ('Te0/2/1', 'L3:MPLOSP D:B L1:DP TO_RO-PIN-CER1_TE0/0/1_PATH1', '10000000000', 'MPLS',
        'OSP', 'DWDM', 'BOTH',
        55, '172.16.25.10')


create table diagrams
(
  uid         int auto_increment primary key,
  name        varchar(50) unique,
  description text

);
drop table diagram_network_devices;
create table diagram_network_devices
(
  uid            int auto_increment primary key,
  diagram_uid    int,
  net_device_uid int,
  x              float,
  y              float,
  foreign key (net_device_uid) references network_devices (uid),
  foreign key (diagram_uid) references diagrams (uid)

);

insert into diagrams(name, description)
values ('RCE_GUATEMALA', 'Red de transporte nacional de Guatemala');

delete
from diagram_network_devices
where uid > 0;

select *
from diagrams;
select *
from network_devices
WHERE hostname LIKE '%SMA%';


select *
from interface_states
where link_state = 'down'
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
       s.state_timestamp,
       i.ip

from network_devices as d
       inner join interfaces as i on d.uid = i.net_device_uid
       inner join (select * from interface_states where DATE(state_timestamp) = DATE(NOW())) as s
                  on s.interface_uid = i.uid
       inner join (select max(uid) as uid from interface_states group by interface_uid) as s2 on s2.uid = s.uid
WHERE net_device_uid = 6
  and state_timestamp >= '2019-05-14 00:00:00'
  and state_timestamp <= '2019-05-14 23:59:00'

select uid
from network_devices
where ip = '172.16.30.1';

drop table users;
create table users
(
  uid      int auto_increment primary key,
  username    varchar(50),
  hash varchar(70)

);




select * from interface_states ORDER  BY uid DESC limit 20;