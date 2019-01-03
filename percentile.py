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
    s.util_in as util_in,util_out as util_out,s.state_timestamp  
    from network_devices as d
    inner join interfaces as i on d.uid = i.net_device_uid 
    inner join interface_states as s on i.uid = interface_uid 
    where s.state_timestamp >='2019-01-01 00:00:00' and s.state_timestamp <'2019-01-31 00:00:00'
    '''
    df = pd.read_sql(sql, con=conection)
    df2 = df[['uid', 'l3_protocol_attr', 'hostname', 'if_index', 'description']].drop_duplicates(subset='uid',
                                                                                                 keep='first')
    print(df2.info())

    df_proceded = (df.groupby(by=['uid'])['util_out', 'util_in'].quantile(.95)).reset_index()
    print(df_proceded.info())
    df_merge = pd.merge(df_proceded, df2, on=['uid'], how='left').sort_values(
        ascending=False, by=['util_out'])
    IPT = df_merge[df_merge['l3_protocol_attr'] == 'IPT'].to_dict(orient='records')

    pprint(len(IPT))
