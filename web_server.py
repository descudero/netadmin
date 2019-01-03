from flask import Flask, render_template
from flask_mysqldb import MySQL
import pandas as pd

app = Flask(__name__)

app.config['MYSQL_HOST'] = '10.250.55.17'
app.config['MYSQL_USER'] = 'net_admin'
app.config['MYSQL_PASSWORD'] = 'Ufinet_2010!'
app.config['MYSQL_DB'] = 'netadmin'
mysql = MySQL(app)


@app.route('/reportes/internet/')
def reporte_internet():
    sql = '''select  
       d.hostname as host,
       i.uid,
       i.if_index as inter,
       left(right(i.description,CHAR_LENGTH(i.description)-20),35) as description,i.l3_protocol as l3p,
       i.l3_protocol_attr as l3a ,
       i.l1_protocol ,
       i.l1_protocol_attr,
       s.util_in as util_in,util_out as util_out,
       (s.input_rate/1073741824) as in_gbs ,
       (s.output_rate/1073741824) as out_gbs
       ,s.state_timestamp  
       from network_devices as d
       inner join interfaces as i on d.uid = i.net_device_uid 
       inner join interface_states as s on i.uid = interface_uid 
       where s.state_timestamp >='2019-01-01 00:00:00' and s.state_timestamp <'2019-01-31 00:00:00'
       '''
    df = pd.read_sql(sql, con=mysql.connection)
    df2 = df[['host', 'uid', 'inter', 'description', 'l3p', 'l3a', 'l1_protocol',
              'l1_protocol_attr']].drop_duplicates(subset='uid', keep='first')
    df_proceded = (
        df.groupby(by=['uid'])['util_out', 'util_in', 'out_gbs', 'in_gbs'].quantile(.95)).round(
        1).reset_index()
    df_merge = pd.merge(df_proceded, df2, on=['uid'], how='left').sort_values(ascending=False, by=['util_out'])
    df_merge.drop(['uid'], axis=1, inplace=True)

    ipts = df_merge[df_merge['l3a'] == 'IPT'].sort_values(by="util_in", ascending=False).to_dict(
        orient='records')

    pnis = df_merge[df_merge['l3a'] == 'PNI'].sort_values(by="util_out", ascending=False).to_dict(
        orient='records')

    ibps = df_merge[df_merge['l3a'] == 'IBP'].sort_values(by="util_out", ascending=False).to_dict(
        orient='records')
    mpls_cm = df_merge[
        (df_merge['l3p'] == 'MPLS') & (df_merge['l1_protocol'] == "CABLE_SUBMARINO")].sort_values(
        by="util_out", ascending=False).to_dict(
        orient='records')
    caches = df_merge[df_merge['l3a'] == 'CDN'].sort_values(by="util_in", ascending=False).to_dict(
        orient='records')

    return render_template('reporte_internet.html', ipts=ipts, ibps=ibps, mpls_cm=mpls_cm, caches=caches, pnis=pnis)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1', debug=True)
