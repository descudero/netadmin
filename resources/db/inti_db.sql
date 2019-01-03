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
create table interface_states
(
  uid             int auto_increment primary key,
  link_state      varchar(50),
  protocol_state  varchar(50),
  input_rate      bigint,
  output_rate     bigint,
  util_in         decimal(10, 2),
  util_out        decimal(10, 2),
  input_errors    bigint,
  output_errors   bigint,
  interface_uid   int,
  state_timestamp datetime,
  foreign key (interface_uid) references interfaces (uid)
);