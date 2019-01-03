from config import Master
from pprint import pprint
import pandas as pd

master = Master(username="test", password="test")

conection = master.db_connect()
with conection.cursor() as cursor:
    sql = '''select  d.hostname,i.uid,i.if_index,i.l3_protocol_attr, s.util_in as util_in,util_out as util_out,s.state_timestamp  
    from network_devices as d
    inner join interfaces as i on d.uid = i.net_device_uid 
    inner join interface_states as s on i.uid = interface_uid 
    where s.state_timestamp >='2019-01-01 00:00:00' and s.state_timestamp <'2019-01-31 00:00:00'
    '''
    df = pd.read_sql(sql, con=conection)
    df2 = df[['uid', 'hostname', 'if_index']]
    df_proceded = (df.groupby(by=['uid'])['util_in', 'util_out'].quantile(.95))
    df_merge = df_proceded.join(other=df2, on="uid", lsuffix='_p')
    print(df_merge)
