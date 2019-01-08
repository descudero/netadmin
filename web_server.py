from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL
import socket
import datetime
import calendar
import time
from collections import OrderedDict
from tools import performance_log
import pymysql.cursors
import pymysql
from pprint import pprint
from collections import defaultdict


import pandas as pd

app = Flask(__name__)

app.config['MYSQL_HOST'] = '10.250.55.17'
app.config['MYSQL_USER'] = 'net_admin'
app.config['MYSQL_PASSWORD'] = 'Ufinet_2010!'
app.config['MYSQL_DB'] = 'netadmin'
mysql = MySQL(app)


def connect_mysql():
    return pymysql.connect(host=app.config['MYSQL_HOST'],
                           user=app.config['MYSQL_USER'],
                           password=app.config['MYSQL_PASSWORD'],
                           db=['MYSQL_DB'],
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)

@app.route('/reportes/internet/', methods=['POST', 'GET'])
def reporte_internet():
    pl = performance_log("json")
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
    pl.flag("json data")

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
    pl.flag("df sql")
    df2 = df[['host', 'uid', 'inter', 'description', 'l3p', 'l3a', 'l1_protocol', 'data_flow',
              'l1_protocol_attr']].drop_duplicates(subset='uid', keep='first')
    df_proceded = (
        df.groupby(by=['uid'])['util_out', 'util_in', 'out_gbs', 'in_gbs'].quantile(percentile)).round(
        1).reset_index()
    pl.flag("df quantile")
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
    tables = filter_summary(df_merge, columns, sort_column=sort_columns)
    pl.flag('filer tables')
    pl.print_intervals()
    return render_template('reporte_internet_percentile.html', titulo=titulo,
                           tables=tables)


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
	   inner join	(select * from interface_states where DATE(state_timestamp)=DATE(NOW())) as s on s.interface_uid= i.uid
           inner join  (select max(uid) as uid from interface_states group by interface_uid) as s2 on s2.uid = s.uid;
           '''
    columns = ['host', 'inter', 'description', 'l1_protocol', 'l1_protocol_attr', 'util_in', 'util_out', 'in_gbs',
               'out_gbs']
    sort_columns = {'CAPACIDADES_TRANSITO_INTERNET': 'util_in', 'CAPACIDADES_DIRECTOS_ASN': 'util_in',
                    'SERVIDORES_CACHE_TERCEROS': 'util_in',
                    'default': 'util_out'}
    titulo = "ESTADO ACTUAL DE CAPACIDADES RELACIONADAS A INTERNET UFINET"
    return render_template('reporte_internet.html', titulo=titulo,
                           tables=filter_summary(pd.read_sql(sql, con=mysql.connection), columns, sort_columns))


def filter_sql(filtro, apply_and=True, table_suffix=""):
    filter_keys = {'CAPACIDADES_TRANSITO_INTERNET': {'l3_protocol_attr': 'IPT'},
                   'CAPACIDADES_DIRECTOS_ASN': {'l3_protocol_attr': 'PNI'},
                   'BGPS_DIRECTOS_INTERNOS_DOWNSTREAM': {'l3_protocol_attr': 'IBP', 'data_flow': 'DOWNSTREAM'},
                   'TRUNCALES_MPLS_DOWNSTREAM': {'l3_protocol': 'MPLS',
                                                 'l1_protocol': 'CABLE_SUBMARINO'
                                                 },
                   'SERVIDORES_CACHE_TERCEROS': {'l3_protocol_attr': 'CDN'}
                   }
    sql_filter = ""

    if filtro in filter_keys:
        if apply_and: sql_filter += " and "
        sql_filter += " and ".join(
            [table_suffix + column + "='" + text + "'" for column, text in filter_keys[filtro].items()])
    return sql_filter


def function_pivot(data_sql, grouping_index=0, column_index=1, value_index=2):
    data = defaultdict(OrderedDict)
    for row in data_sql:
        data[str(row[grouping_index])][str(row[column_index])] = float(row[value_index])
    data2 = [
        {'x': list(serie.keys()), 'y': list(serie.values()), 'name': serie_name, 'stackgroup': 'dos',
         'fill': 'tonexty', 'hoverlabel': {'namelength': -1}}
        for serie_name, serie in data.items()]
    return data2


@app.route('/reportes/json/interface_group_day/', methods=['POST', 'GET'])
def json_data_graph():
    request.get_json()
    month = datetime.date.today().month
    year = datetime.date.today().year
    last_day = calendar.monthrange(year, month)[1]
    date_start = request.json.get('date_start', '{year}-{month}-{day}'.format(year=year, month=month, day=1))
    if date_start == '': date_start = '{year}-{month}-{day}'.format(year=year, month=month, day=1)
    date_end = request.json.get('date_end', '{year}-{month}-{day}'.format(year=year, month=month, day=last_day))
    if date_end == '': date_end = '{year}-{month}-{day}'.format(year=year, month=month, day=last_day)
    in_out = request.json.get('in_out', 'input')
    sql_text = filter_sql(request.json['group'], apply_and=True, table_suffix="i.")
    pl = performance_log("json")
    sql = '''select  
        CONCAT(d.hostname, " > ", i.if_index) AS int_host ,
        DATE(s.state_timestamp) as date_poll,
        max((s.{3}_rate/1073741824)) as value ,
        left(right(i.description,CHAR_LENGTH(i.description)-20),20) as description
        ,i.l3_protocol,
        i.l3_protocol_attr,
        i.l1_protocol,
        i.l1_protocol_attr
        from network_devices as d
        inner join interfaces as i on d.uid = i.net_device_uid 
        inner join interface_states as s on i.uid = interface_uid 
        where s.state_timestamp >='{0}' and s.state_timestamp <='{1}' {2}
        group by d.hostname,i.uid,i.if_index,description,i.l3_protocol_attr,i.l1_protocol,i.l1_protocol_attr,i.l3_protocol,date_poll
        order BY date_poll ASC;
        '''.format(date_start, date_end, sql_text, in_out)
    with mysql.connection.cursor() as cursor:
        cursor.execute(sql)
        data_sql = cursor.fetchall()
        pl.new_flag("load normal sql")
        data = function_pivot(data_sql)
        pl.new_flag("pivot")

    jdata = jsonify(data)
    pl.new_flag("j data")
    # pl.print_intervals()
    return jdata


@app.route('/favicon.ico')
def flour():
    return ""

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
