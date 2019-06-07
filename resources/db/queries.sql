select *
from bgp_neighbors


select *
from network_devices


select * from diagram_sta

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


SELECT i.net_device_uid,
       i.uid      as uid,
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
       inner join (select * from interface_states where DATE(state_timestamp) = DATE(NOW()))
  as s on s.interface_uid = i.uid
       inner join (select max(uid) as uid from interface_states group by interface_uid) as s2 on s2.uid = s.uid
WHERE net_device_uid in
      (48, 54, 41, 66, 49, 644, 40, 39, 46, 53, 63, 62, 42, 6, 37, 64, 55, 69, 50, 5, 606, 25, 4, 44, 1, 26, 36, 2,
       12501, 59, 8, 52, 60, 65, 61, 56, 7, 155743, 51, 68, 58, 3, 67, 38, 580, 57, 648, 70, 45)
  and state_timestamp >= '2019-06-03 00:00:00'
  and state_timestamp <= '2019-06-03 23:59:00'


SELECT uid,state_timestamp
FROM diagram_states
WHERE diagram_uid = 1
ORDER BY uid DESC
limit 1

SELECT COUNT(uid)
FROM diagram_state_adjacencies
WHERE diagram_state_uid = 43

select *
from network_devices
where hostname like 'RO_PCO_CER1';



SELECT i.net_device_uid,
       i.uid      as uid,
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
       inner join (select * from interface_states where DATE(state_timestamp) = DATE(NOW()))
  as s on s.interface_uid = i.uid
       inner join (select max(uid) as uid from interface_states group by interface_uid) as s2 on s2.uid = s.uid
WHERE net_device_uid IN
      (60, 57, 41, 56, 644, 36, 38, 64, 69, 45, 6, 68, 67, 48, 42, 51, 606, 40, 62, 61, 46, 37, 65, 55, 66, 49, 26, 58,
       52, 648, 39, 3, 8, 50, 2, 155743, 59, 12501, 70, 25, 53, 4, 5, 54, 1, 580, 44, 0, 7)
  and state_timestamp >= '2019-06-03 00:00:00'
  and state_timestamp <= '2019-06-03 23:59:00'
  2019-06-03 17:42:09
    ,411:WARNING:db.Devices:dict_from_sql
SELECT i.net_device_uid,
       i.uid      as uid,
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
       inner join (select * from interface_states where DATE(state_timestamp) = DATE(NOW()))
  as s on s.interface_uid = i.uid
       inner join (select max(uid) as uid from interface_states group by interface_uid) as s2 on s2.uid = s.uid
WHERE net_device_uid IN
      (45, 3, 155743, 69, 52, 7, 38, 68, 40, 25, 26, 12501, 37, 55, 6, 644, 53, 63, 46, 4, 64, 54, 57, 8, 1, 65, 51, 42,
       56, 49, 66, 44, 36, 41, 60, 61, 58, 580, 62, 48, 59, 67, 5, 50, 606, 2, 70, 0, 648)
  and state_timestamp >= '2019-06-03 00:00:00'
  and state_timestamp <= '2019-06-03 23:59:00'

UPDATE netadmin.network_devices
SET hostname='RO-NIC-EDGE2',
    ip='172.16.30.235',
    country='NICARAGUA',
    area='PLAZAINTER',
    roll='[LSR]'
WHERE uid = '12501'


commit


select *
from interfaces
order by uid DESC
limit 1300

set foreign_key_checks = 0;
delete
from interface_states
where interface_uid in (
                        135289,
                        135290,
                        135291,
                        135292,
                        135518,
                        135536
  );

delete
from diagram_state_adjacencies
where interface_1_uid in (
                          135289,
                          135290,
                          135291,
                          135292,
                          135518,
                          135536
  )
   or interface_2_uid
  in (
      135289,
      135290,
      135291,
      135292,
      135518,
      135536
        );

delete
from interfaces
where uid in (
              135289,
              135290,
              135291,
              135292,
              135518,
              135536
  );

select i.uid,i.if_index,i.ip,i.description
from network_devices as ns
       inner join interfaces as i on i.net_device_uid = ns.uid
where ns.ip = '172.16.30.3';

select *
from interfaces
where if_index like '%BD%'
   OR if_index like '%Po%'
order by uid DESC
limit 25;
select *
from interface_states
where interface_uid = 129585;

select *
from network_devices as ns
       inner join interfaces as i on i.net_device_uid = ns.uid
where ns.ip = '172.19.8.60';


