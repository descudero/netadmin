from config import Master
from pprint import pprint
import pandas as pd
import numpy as np


master = Master(username="test", password="test")

conection = master.db_connect()
with conection.cursor() as cursor:
    sql = '''select  
    d.hostname,i.uid,i.if_index,
    left(right(i.description,CHAR_LENGTH(i.description)-20),20) as description,i.l3_protocol,
    i.l3_protocol_attr,i.l1_protocol,i.l1_protocol_attr,
    s.util_in as util_in,s.util_out as util_out,
   (s.input_rate/1073741824) as input_rate_gbs ,(s.output_rate/1073741824) as output_rate_gbs,
    s.state_timestamp
    from network_devices as d
    inner join interfaces as i on d.uid = i.net_device_uid 
    inner join interface_states as s on i.uid = interface_uid 
    where s.state_timestamp >='2019-01-01 00:00:00' and s.state_timestamp <'2019-01-31 00:00:00'
    '''
    df = pd.read_sql(sql, con=conection)
    df['filter_special'] = df['state_timestamp'].apply(
        lambda x: '{0}-{1}-{2}-{3}'.format(x.year, x.month, x.day, x.hour))
    df['month'] = df['state_timestamp'].apply(lambda x: x.month)
    df['day'] = df['state_timestamp'].apply(lambda x: x.day)
    df['year'] = df['state_timestamp'].apply(lambda x: x.year)
    df['day'] = df['state_timestamp'].apply(lambda x: x.day)

    df2 = df[['uid', 'l3_protocol_attr', 'hostname', 'if_index', 'description', 'state_timestamp']].drop_duplicates(
        subset='uid',
                                                                                                 keep='first')

