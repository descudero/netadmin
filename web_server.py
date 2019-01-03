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
       d.hostname,i.uid,i.if_index,
       left(right(i.description,CHAR_LENGTH(i.description)-20),35) as description,i.l3_protocol,
       i.l3_protocol_attr,i.l1_protocol,i.l1_protocol_attr,
       s.util_in as util_in,util_out as util_out,s.state_timestamp  
       from network_devices as d
       inner join interfaces as i on d.uid = i.net_device_uid 
       inner join interface_states as s on i.uid = interface_uid 
       where s.state_timestamp >='2019-01-01 00:00:00' and s.state_timestamp <'2019-01-31 00:00:00'
       '''
    df = pd.read_sql(sql, con=mysql.connection)
    df2 = df[['hostname', 'uid', 'if_index', 'description', 'l3_protocol', 'l3_protocol_attr', 'l1_protocol',
              'l1_protocol_attr']].drop_duplicates(subset='uid', keep='first')
    df_proceded = (df.groupby(by=['uid'])['util_out', 'util_in'].quantile(.95)).round(2).reset_index()
    df_merge = pd.merge(df_proceded, df2, on=['uid'], how='left').sort_values(ascending=False, by=['util_out'])

    ipts = df_merge[df_merge['l3_protocol_attr'] == 'IPT'].sort_values(by="util_in", ascending=False).to_dict(
        orient='records')

    pnis = df_merge[df_merge['l3_protocol_attr'] == 'PNI'].sort_values(by="util_out", ascending=False).to_dict(
        orient='records')

    ibps = df_merge[df_merge['l3_protocol_attr'] == 'IBP'].sort_values(by="util_out", ascending=False).to_dict(
        orient='records')
    mpls_cm = df_merge[
        (df_merge['l3_protocol'] == 'MPLS') & (df_merge['l1_protocol'] == "CABLE_SUBMARINO")].sort_values(
        by="util_out", ascending=False).to_dict(
        orient='records')
    caches = df_merge[df_merge['l3_protocol_attr'] == 'CDN'].sort_values(by="util_in", ascending=False).to_dict(
        orient='records')

    return render_template('reporte_internet.html', ipts=ipts, ibps=ibps, mpls_cm=mpls_cm, caches=caches, pnis=pnis)


if __name__ == '__main__':
    app.run(port=80, debug=True)
