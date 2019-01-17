create table device_parts
(
  uid            int auto_increment primary key,
  net_device_uid int,
  serial_number  varchar(40),
  vid            varchar(10),
  pid            varchar(30),
  name           varchar(50),
  local_name     varchar(50),
  foreign key (net_device_uid) references network_devices (uid)
);

ALTER TABLE device_parts
  ADD column time_polled datetime;

select *
from device_parts;
ALTER TABLE device_parts
  MODIFY
    column pid varchar(50);


select count(*)
from network_devices
where platform like 'CiscoXR'
select *
from device_parts as p1
       inner join (select max(time_polled)
                            as max_time
                   from device_parts
                   where net_device_uid = 5) as t on p1.time_polled = max_time
where net_device_uid = 5