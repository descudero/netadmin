from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL
import socket
import datetime
import calendar


import pandas as pd

app = Flask(__name__)

app.config['MYSQL_HOST'] = '10.250.55.17'
app.config['MYSQL_USER'] = 'net_admin'
app.config['MYSQL_PASSWORD'] = 'Ufinet_2010!'
app.config['MYSQL_DB'] = 'netadmin'
mysql = MySQL(app)


@app.route('/reportes/internet/', methods=['POST', 'GET'])
def reporte_internet():
    percentile = .95
    month = datetime.date.today().month
    year = datetime.date.today().year
    last_day = calendar.monthrange(year, month)[1]
    initial_date = '{year}-{month}-{day} 00:00:00'.format(year=year, month=month, day=1)
    end_date = '{year}-{month}-{day} 23:59:59'.format(year=year, month=month, day=last_day)
    if request.method == 'POST':
        if 'initial_date' in request.form:
            if request.form['initial_date'] == '':
                initial_date = '{year}-{month}-{day} 00:00:00'.format(year=year, month=month, day=1)
            else:
                initial_date += ' 00:00:00'

        if 'end_date' in request.form:
            if request.form['end_date'] == '':
                end_date = '{year}-{month}-{day} 23:59:59'.format(year=year, month=month, day=last_day)
            else:
                end_date += ' 23:59:59'

        if 'percentile' in request.form:
            try:
                percentile = float(request.form['percentile'])
            except:
                percentile = .95
    if percentile > .99999:
        percentile = .95
    print(initial_date, end_date)

    sql = '''select  
       d.hostname as host,
       i.uid,
       i.if_index as inter,
       right(i.description,CHAR_LENGTH(i.description)-20) as description,i.l3_protocol as l3p,
       i.l3_protocol_attr as l3a ,
       i.l1_protocol ,
       i.l1_protocol_attr,
       i.data_flow,
       s.util_in as util_in,util_out as util_out,
       (s.input_rate/1073741824) as in_gbs ,
       (s.output_rate/1073741824) as out_gbs
       ,s.state_timestamp  
       from network_devices as d
       inner join interfaces as i on d.uid = i.net_device_uid 
       inner join interface_states as s on i.uid = interface_uid 
       where s.state_timestamp >='{initial_date}' and s.state_timestamp <'{end_date}'
       '''.format(initial_date=initial_date, end_date=end_date)
    df = pd.read_sql(sql, con=mysql.connection)

    df2 = df[['host', 'uid', 'inter', 'description', 'l3p', 'l3a', 'l1_protocol', 'data_flow',
              'l1_protocol_attr']].drop_duplicates(subset='uid', keep='first')
    df_proceded = (
        df.groupby(by=['uid'])['util_out', 'util_in', 'out_gbs', 'in_gbs'].quantile(percentile)).round(
        1).reset_index()
    df_merge = pd.merge(df_proceded, df2, on=['uid'], how='left').sort_values(ascending=False, by=['util_out'])
    df_merge.drop(['uid'], axis=1, inplace=True)
    columns = ['host', 'inter', 'description', 'l1_protocol', 'l1_protocol_attr', 'util_in', 'util_out', 'in_gbs',
               'out_gbs']
    sort_columns = {'CAPACIDADES_TRANSITO_INTERNET': 'util_in', 'CAPACIDADES_DIRECTOS_ASN': 'util_in',
                    'SERVIDORES_CACHE_TERCEROS': 'util_in',
                    'default': 'util_out'}
    titulo = "Percentil {percentile}% de {fecha_inicial} a {fecha_final} DE CAPACIDADES RELACIONADAS A INTERNET UFINET" \
        .format(percentile=round(percentile * 100, 2), fecha_inicial=initial_date.split(" ")[0],
                fecha_final=end_date.split(" ")[0])
    return render_template('reporte_internet_percentile.html', titulo=titulo,
                           tables=filter_summary(df_merge, columns, sort_column=sort_columns))


@app.route('/test_css')
def css_test():
    return render_template('layout.html', titulo="prueba")


@app.route('/reportes/graphs')
def graph():
    return render_template('graphs.html')

@app.route('/reportes/internet/actual')
def reporte_internet_actual():
    sql = '''select  
           d.hostname as host,
           i.if_index as inter,
           right(i.description,CHAR_LENGTH(i.description)-20)as description,i.l3_protocol as l3p,
           i.l3_protocol_attr as l3a ,
           i.l1_protocol ,
           i.l1_protocol_attr,i.data_flow,
           s.util_in as util_in,s.util_out as util_out,
           (s.input_rate/1073741824) as in_gbs ,
           (s.output_rate/1073741824) as out_gbs
           ,s.state_timestamp  
           from network_devices as d
           inner join interfaces as i on d.uid = i.net_device_uid 
           inner join interface_states as s on i.uid = interface_uid 
           LEFT JOIN interface_states  AS s2
           ON (s.interface_uid = s2.interface_uid  AND s.state_timestamp < s2.state_timestamp)
           WHERE s2.state_timestamp IS NULL;
           '''
    columns = ['host', 'inter', 'description', 'l1_protocol', 'l1_protocol_attr', 'util_in', 'util_out', 'in_gbs',
               'out_gbs']
    sort_columns = {'CAPACIDADES_TRANSITO_INTERNET': 'util_in', 'CAPACIDADES_DIRECTOS_ASN': 'util_in',
                    'SERVIDORES_CACHE_TERCEROS': 'util_in',
                    'default': 'util_out'}
    titulo = "ESTADO ACTUAL DE CAPACIDADES RELACIONADAS A INTERNET UFINET"
    return render_template('reporte_internet.html', titulo=titulo,
                           tables=filter_summary(pd.read_sql(sql, con=mysql.connection), columns, sort_columns))


def filter_summary(sql_dataframe, columns, sort_column={}):
    filter_keys = {'CAPACIDADES_TRANSITO_INTERNET': {'l3a': 'IPT'},
                   'CAPACIDADES_DIRECTOS_ASN': {'l3a': 'PNI'},
                   'BGPS_DIRECTOS_INTERNOS_DOWNSTREAM': {'l3a': 'IBP', 'data_flow': 'DOWNSTREAM'},
                   'TRUNCALES_MPLS_DOWNSTREAM': {'l3p': 'MPLS',
                                                 'l1_protocol': 'CABLE_SUBMARINO'
                                                 },
                   'SERVIDORES_CACHE_TERCEROS': {'l3a': 'CDN'}
                   }
    results = {}
    for key, filters in filter_keys.items():
        results[key] = sql_dataframe.copy()
        for column, value in filters.items():
            df = results[key]
            df = df[df[column] == value]
            results[key] = df
        if (key in sort_column):
            results[key] = results[key].sort_values(by=sort_column[key], ascending=False)
        elif ('default' in sort_column):
            results[key] = results[key].sort_values(by=sort_column['default'], ascending=False)

        results[key] = results[key][columns].to_dict(orient='records')
    return results


if __name__ == '__main__':
    if socket.gethostname() == 'gu-app-labs':
        port = 8080
        host = '10.250.55.17'
    else:
        port = 8080
        host = '127.0.0.1'
    app.run(port=port, host=host, debug=True)
