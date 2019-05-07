set foreign_key_checks = 0;
drop table network_devices;
set foreign_key_checks = 1;
create table network_devices
(
  uid      int auto_increment primary key,
  ip       varchar(50) unique,
  hostname varchar(100) unique,
  platform varchar(30)
);
set foreign_key_checks = 0;
drop table interfaces;
set foreign_key_checks = 1;
create table interfaces
(
  uid              int auto_increment primary key,
  if_index         varchar(50),
  description      varchar(255),
  bandwith         bigint,
  l3_protocol      varchar(50),
  l3_protocol_attr varchar(50),
  l1_protocol      varchar(50),
  l1_protocol_attr varchar(50),
  data_flow        varchar(50),
  net_device_uid   int,
  foreign key (net_device_uid) references network_devices (uid)
);

set foreign_key_checks = 0;
drop table interface_states;
set foreign_key_checks = 1;

create table bgp_neighbors
(
  uid            int auto_increment primary key,
  ip             varchar(50),
  asn            int,
  address_family varchar(50),
  net_device_uid int,
  foreign key (net_device_uid) references network_devices (uid)
);


set foreign_key_checks = 0;
drop table bgp_neighbor_states;
set foreign_key_checks = 1;
create table bgp_neighbor_states
(
  uid                 int auto_increment primary key,
  state               VARCHAR(50),
  last_error          VARCHAR(50),
  advertised_prefixes int,
  accepted_prefixes   int,
  state_timestamp     datetime,
  bgp_neighbor_uid    int,
  foreign key (bgp_neighbor_uid) references bgp_neighbors (uid)
);

select *
from bgp_neighbor_states


UPDATE interfaces
SET ip = '127.0.0.1'
WHERE uid = '60552'