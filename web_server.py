from flask import Flask, render_template, request, jsonify
import networkx as nx
import socket
import datetime
import calendar
import time
from collections import OrderedDict
from tools import PerformanceLog
import pymysql.cursors
import pymysql
from pprint import pprint
from collections import defaultdict
from config.Master import Master
from model.claseClaro import Claro
from model.InternetServiceProvider import InternetServiceProvider as ISP
import logging
from model.CiscoXR import CiscoXR
from support.ConfigTemplate import ConfigTemplate
import pandas as pd
from model.ospf_database import ospf_database
from model.InterfaceUfinet import InterfaceUfinet
from model.BGPNeigbor import BGPNeighbor
from operator import itemgetter
from model.Diagram import Diagram
from model.Devices import Devices
from model.CiscoIOS import CiscoIOS
from threading import Thread

app = Flask(__name__)
app.config['SECRET_KEY'] = "autenticacion basica"
app.config['MYSQL_HOST'] = '10.250.55.17'
app.config['MYSQL_USER'] = 'net_admin'
app.config['MYSQL_PASSWORD'] = 'Ufinet_2010!'
app.config['MYSQL_DB'] = 'netadmin'
master = Master()
mysql = master
isp = ISP()
isp.master = master
weblog = logging.getLogger("web.netadmin.app")
per = logging.getLogger("performance.netadmin.app")
verbose = logging.getLogger("verbose.netadmin.app")


def connect_mysql():
    return pymysql.connect(host=app.config['MYSQL_HOST'],
                           user=app.config['MYSQL_USER'],
                           password=app.config['MYSQL_PASSWORD'],
                           db=['MYSQL_DB'],
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)


@app.route('/reportes/bgp_neighbors/view/<int:uid>', )
def bgp_peer_view(uid):
    return render_template('bgp_peer_view.html', uid=uid)


@app.route('/reportes/bgp_neighbors/json/<int:uid>', methods=['POST'])
def bgp_peer_json(uid):
    bgp_peer = BGPNeighbor.load_uid(isp=isp, uid=uid)
    request.get_json()
    date_start_json = request.json['date_start']
    date_end_json = request.json['date_end']
    date_start = (str(datetime.date.today()) if date_start_json is '' else date_start_json) + ' 00:00:00'
    date_end = (str(datetime.date.today()) if date_end_json is '' else date_end_json) + ' 23:59:00'
    data_peer = bgp_peer.load_states(date_start, date_end)

    x = [str(state['state_timestamp'].strftime("%Y-%m-%d %H:%M:%S")) for state in data_peer]
    y = [state['accepted_prefixes'] for state in data_peer]
    state_data = [
        {"bgp_state": state['state'], 'last_know_error': state['last_error'], 'time': state['state_timestamp']} for
        state in data_peer]
    state_data.sort(key=itemgetter('time'), reverse=True)
    name = f'PREFIJOS BGP PEER {bgp_peer.ip} EN {bgp_peer.parent.hostname} {date_start} A {date_end}'
    data = {}
    traces = [{'x': x, 'y': y, 'name': name, 'stackgroup': 'dos',
               'fill': 'tonexty', 'hoverlabel': {'namelength': -1}}]
    data['traces'] = traces
    data['state_data'] = state_data
    data['title'] = name
    return jsonify(data)


@app.route('/reportes/bgp_neighbors/peers/', )
def bgp_peers():
    return render_template('bgp_peer_list.html')


@app.route('/reportes/bgp_neighbors/peers/json', methods=['POST'])
def bgp_peers_json():
    request.get_json()
    date_start_json = request.json['date_start']
    date_end_json = request.json['date_start']
    date_start = (str(datetime.date.today()) if date_start_json is '' else date_start_json) + ' 00:00:00'
    date_end = (str(datetime.date.today()) if date_end_json is '' else date_end_json) + ' 23:59:00'
    data = dict()

    data['bg.asn'] = request.json['asn']
    data['bg.ip'] = request.json['ip']
    data['nd.hostname'] = request.json['hostname']
    data['bs.state'] = request.json['state']
    other_filter = ""

    counter = 0
    pprint(data)
    for column, value in data.items():
        if value is not '':
            if counter != 0:
                other_filter += f" AND "
            else:
                counter += 1
            other_filter += f" {column} LIKE '%{value}%' "

    data = BGPNeighbor.bgp_peers_from_db(master=master, date_start=date_start, date_end=date_end,
                                         other_filters=other_filter)
    return jsonify(data)


@app.route('/reportes/interfaces/regionales/')
def interfaces_regionales():
    return render_template('interfaces_regionales.html')


@app.route('/reportes/interfaces/regionales/json', methods=['POST'])
def json_interfaces_cisco():
    request.get_json()
    month = datetime.date.today().month
    year = datetime.date.today().year
    last_day = calendar.monthrange(year, month)[1]
    initial_date = '{year}-{month}-{day} 00:00:00'.format(year=year, month=month, day=1) \
        if request.json['initial_date'] == '' else request.json['initial_date'] + ' 00:00:00'
    end_date = '{year}-{month}-{day} 23:59:59'.format(year=year, month=month, day=last_day) \
        if request.json['end_date'] == '' else request.json['end_date'] + ' 00:00:00'

    cantidad_interfaces = int(request.json['cantidad_interfaces'])
    grupo_interfaces = request.json['grupo_interfaces']
    weblog.warning(f'InterfaceUfinet.FILTERS_GROUP[grupo_interfaces] {InterfaceUfinet.FILTERS_GROUP[grupo_interfaces]}')
    data = InterfaceUfinet.interface_states_data_by_date(master=master, initial_date=initial_date, end_date=end_date,
                                                         filter_keys=InterfaceUfinet.FILTERS_GROUP[grupo_interfaces])
    data_grupo = data[grupo_interfaces]
    cantidad_interfaces = cantidad_interfaces - 1 if len(data_grupo) >= cantidad_interfaces else len(
        cantidad_interfaces) - 1
    return jsonify(data_grupo[0:cantidad_interfaces])


@app.route('/reportes/internet/json', methods=['POST'])
def data_interfaces():
    request.get_json()
    grupo_interfaces = request.json['grupo_interfaces']
    month = datetime.date.today().month
    year = datetime.date.today().year
    last_day = calendar.monthrange(year, month)[1]
    initial_date = '{year}-{month}-{day} 00:00:00'.format(year=year, month=month, day=1) \
        if request.json['initial_date'] == '' else request.json['initial_date'] + ' 00:00:00'
    end_date = '{year}-{month}-{day} 23:59:59'.format(year=year, month=month, day=last_day) \
        if request.json['end_date'] == '' else request.json['end_date'] + ' 00:00:00'

    data = InterfaceUfinet.interface_states_data_by_date(master=master, initial_date=initial_date, end_date=end_date,
                                                         filter_keys=InterfaceUfinet.FILTERS_GROUP[grupo_interfaces])

    pass


@app.route('/reportes/internet/nuevo', methods=['POST', 'GET'])
def reporte_internet_filtrado():
    return render_template('reporte_interfaces_filtradas.html')


@app.route('/reportes/internet/json_group_interfaces', methods=['POST'])
def json_group_interfaces():
    request.get_json()
    pprint(request.json)
    group_interfaces = request.json['group_interfaces']
    month = datetime.date.today().month
    year = datetime.date.today().year
    last_day = calendar.monthrange(year, month)[1]
    initial_date = '{year}-{month}-{day} 00:00:00'.format(year=year, month=month, day=1) \
        if request.json['initial_date'] == '' else request.json['initial_date'] + ' 00:00:00'
    end_date = '{year}-{month}-{day} 23:59:59'.format(year=year, month=month, day=last_day) \
        if request.json['end_date'] == '' else request.json['end_date'] + ' 00:00:00'

    data = InterfaceUfinet.interface_states_data_by_date_query(master=master, initial_date=initial_date,
                                                               end_date=end_date,
                                                               sql_filters=InterfaceUfinet.FILTERS_GROUP[
                                                                   group_interfaces]
                                                               , sort=InterfaceUfinet.ORDER_BY_INTERFFACE_GROUPS[
            group_interfaces])

    return jsonify(data)


@app.route('/reportes/internet/', methods=['POST', 'GET'])
def reporte_internet():
    pl = PerformanceLog("json")
    percentile = .95
    month = datetime.date.today().month
    year = datetime.date.today().year
    last_day = calendar.monthrange(year, month)[1]
    initial_date = '{year}-{month}-{day} 00:00:00'.format(year=year, month=month, day=1)
    end_date = '{year}-{month}-{day} 23:59:59'.format(year=year, month=month, day=last_day)
    weblog.debug(":Reporte_internet: calculated ID {0},ED {1}".format(initial_date, end_date))
    if request.method == 'POST':
        if 'initial_date' in request.form:
            if request.form['initial_date'] == '':
                initial_date = '{year}-{month}-{day} 00:00:00'.format(year=year, month=month, day=1)
            else:
                initial_date = request.form['initial_date'] + ' 00:00:00'

        if 'end_date' in request.form:
            if request.form['end_date'] == '':
                end_date = '{year}-{month}-{day} 23:59:59'.format(year=year, month=month, day=last_day)
            else:
                end_date = request.form['end_date'] + ' 23:59:59'

        if 'percentile' in request.form:
            try:
                percentile = float(request.form['percentile'])
            except:
                percentile = .95
    if percentile > .99999:
        percentile = .95
    weblog.debug(":Reporte_internet: final ID {0}, ED {1}".format(initial_date, end_date))

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
       (s.input_rate/1000000000) as in_gbs ,
       (s.output_rate/1000000000) as out_gbs
       ,s.state_timestamp  
       from network_devices as d
       inner join interfaces as i on d.uid = i.net_device_uid 
       inner join interface_states as s on i.uid = interface_uid 
       where s.state_timestamp >='{initial_date}' and s.state_timestamp <'{end_date}'
       '''.format(initial_date=initial_date, end_date=end_date)

    df = pd.read_sql(sql, con=master.db_connect())
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
    pl.flag('end')
    if (pl.time_flag() > 2000):
        per.warning("JSON_GRAPH TO MUCH TIME " + pl.format_time_lapse())
    else:
        per.debug("JSON_GRAPH " + pl.format_time_lapse())

    return render_template('reporte_internet_percentile.html', percentile=percentile, titulo=titulo,
                           end_date=end_date.split(" ")[0], initial_date=initial_date.split(" ")[0],
                           tables=tables)


@app.route('/test_css')
def css_test():
    return render_template('layout.html', titulo="prueba")


@app.route('/diagramas/ospf')
def diagramas():
    return render_template('diagramas.html')


@app.route('/diagramas/te_json', methods=['POST'])
def te_json():
    request.get_json()
    data = request.json['data']
    nodes = {edge['from_id'] for edge in data} | {edge['to_id'] for edge in data}
    G = nx.Graph()
    G.add_nodes_from(nodes)

    for edge in data:
        G.add_edge(edge['to_id'], edge['from_id'])
        G.edges[edge['to_id'], edge['from_id']]['attr'] = {str(edge['to_id']) + 'ip': edge['to_ip'],
                                                           str(edge['from_id']) + 'ip': edge['from_ip']}
    final = [node for node in G.nodes if len(G.edges(node)) == 1]

    shortest = nx.shortest_path(G, source=final[0], target=final[1])
    dev1 = list(Devices.load_uids(master=master, uids=[final[0]]))[0]
    dev2 = list(Devices.load_uids(master=master, uids=[final[1]]))[0]
    ip_go = []
    ip_return = []
    for index in range(len(shortest) - 1):
        ip_return.append(G.edges[shortest[index], shortest[index + 1]]['attr'][f'{shortest[index]}ip'])
        ip_go.append(G.edges[shortest[index], shortest[index + 1]]['attr'][f'{shortest[index + 1]}ip'])
    ip_return = list(reversed(ip_return))
    path1 = f"explicit-path name {dev1.hostname}_{dev2.hostname} <br>"
    path2 = f"explicit-path name {dev2.hostname}_{dev1.hostname} <br>"
    print(dev1.platform)
    print(dev2.platform)

    for index, hop in enumerate(ip_go):
        if dev1.platform == "CiscoXR":
            path1 += f'index {(index + 1) * 5} '
        path1 += f"next-address {hop} <br>"
    for index, hop in enumerate(ip_return):
        if dev2.platform == "CiscoXR":
            path2 += f'index {(index + 1) * 5} '
        path2 += f"next-address {hop} <br>"

    path1 = dev1.new_ip_explicit_path(to_device=dev2, ip_hops=ip_go).replace("\n", "<br>")
    path2 = dev2.new_ip_explicit_path(to_device=dev1, ip_hops=ip_return).replace("\n", "<br>")
    path1 = f' <h3>{dev1.hostname} {dev1.ip}</h3> <br> {path1}'
    path2 = f' <h3>{dev2.hostname} {dev2.ip}</h3> <br> {path2}'
    return jsonify({"a-b": ip_go, 'b-a': ip_return, "a": final[0], "b": final[1], "str_a": path1, "str_b": path2})


@app.route('/diagramas/prueba_json', methods=['POST'])
def ospf_json_vs():
    isp = ISP()
    isp.master = master
    request.get_json()
    saved = request.json['saved']
    date = request.json['date'].replace("-", "")

    if date == "" and saved != "actual":
        date = time.strftime("%Y%m%d")
    elif saved == "actual":
        date = time.strftime("%Y%m%d")

    pl = PerformanceLog("json_diagram")

    datos_red = {"_ospf_ufinet_regional": {
        "ip_seed_router": "172.16.30.15",
        "shelve_name": "shelves/" + date + "_ospf_ufinet_regional"
        , 'network_name': '_ospf_ufinet_regional'
    }, "guatemala": {
        "ip_seed_router": "172.17.22.52",
        "shelve_name": "shelves/" + date + "guatemala",
        "process_id": '502', "area": '502008', 'network_name': 'RCE_GUATEMALA'
    }, "el_salvador": {
        "ip_seed_router": "172.17.23.11",
        "shelve_name": "shelves/" + date + "el_salvador",
        "process_id": '503', "area": '503001', 'network_name': 'RCE_EL_SALVADOR'
    }, "nicaragua": {
        "ip_seed_router": "172.17.25.1",
        "shelve_name": "shelves/" + date + "nicaragua",
        "process_id": '1', "area": '50501', 'network_name': 'RCE_NICARAGUA'
    }, "honduras": {
        "ip_seed_router": "172.17.24.5",
        "shelve_name": "shelves/" + date + "honduras",
        "process_id": '504', "area": '504002', 'network_name': 'RCE_HONDURAS'
    }, "costa_rica": {
        "ip_seed_router": "172.17.26.2",
        "shelve_name": "shelves/" + date + "costa_rica",
        "process_id": '1', "area": '506001', 'network_name': 'RCE_COSTA_RICA'
    }
        , "panama": {
            "ip_seed_router": "172.17.27.1",
            "shelve_name": "shelves/" + date + "guatemala",
            "process_id": '507', "area": '507001', 'network_name': 'RCE_PANAMA'
        }

    }
    parameters = datos_red[request.json['network']]
    verbose.warning(parameters)
    if saved == "actual":
        verbose.warning(parameters)
        data = isp.ospf_topology_vs(**parameters)
    else:
        try:
            verbose.warning(parameters)
            data = ospf_database.get_vs_from_shelve(shelve_name=parameters["shelve_name"])
            verbose.warning(data)
        except Exception as e:
            weblog.warning(f'ospf_json_vs  date {date} {e}')
            verbose.warning(f'ospf_json_vs  date {date} {e}')
            data = {'nodes': {'id': 0, "label": "NO DATA DATE"}, 'edges': {}, "options": {}}

    pl.flag("end")
    per.info("OSPF JSON TIM " + str(pl.format_time_lapse()))

    return jsonify(data)


@app.route('/reportes/inventario/xr')
def reporte_inventario_xr():
    master = Master()
    devices = CiscoXR.devices(master=master)
    devices_dict = [{"ip": device.ip, "hostname": device.hostname, "platform": device.platform} for device in devices]
    weblog.info("reporte_inventario: {0} dispositivos".format(len(devices_dict)))
    titulo = "Inventario de Equipos XR"

    return render_template('inventario.html', titulo=titulo, devices=devices_dict
                           )


@app.route('/reportes/inventario/xr_json', methods=['POST'])
def json_inventory_per_type():
    request.get_json()
    ip = request.json['ip']
    attr = request.json['attr']
    verbose.critical(ip)
    device = CiscoXR(ip=ip, display_name="", master=master, platform="")
    device.set_chassis(from_db=True)
    return jsonify([getattr(device.chassis, attr)])


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
           (s.input_rate/1000000000) as in_gbs ,
           (s.output_rate/1000000000) as out_gbs
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
                           tables=filter_summary(pd.read_sql(sql, con=master.db_connect()), columns, sort_columns))


@app.route("/prueba/json/grafica")
def prueba_json():
    return render_template("test_graficas.html")


@app.route("/utilidades/plantillas_configuracion")
def config_templates():
    return render_template("config_template.html")


@app.route("/utilidades/plantillas_disponibles", methods=['POST', "GET"])
def config_templates_filter():
    device_type = request.json['device_type']
    try:
        return jsonify([template for template in ConfigTemplate.get_all_templates_names() if device_type in template])
    except Exception as e:
        weblog.warning(f"error config_templates_filter {e}")
        return jsonify(list())


@app.route("/utilidades/template_fields", methods=['POST', "GET"])
def json_template_names():
    template_name = request.json['template_name']
    template = ConfigTemplate(template_name=template_name)

    try:
        return jsonify(template.fields)
    except Exception as e:
        weblog.warning(f"error json_template_names {e}")
        return jsonify(list())


@app.route("/utilidades/render_config_template", methods=['POST', "GET"])
def reder_config_template():
    template_name = request.json['template_name']
    form_data = request.json['form_data']
    template = ConfigTemplate(template_name=template_name)
    weblog.warning(form_data)
    text = template.render_html(values=form_data)
    weblog.warning(text)
    try:
        return jsonify({'config': text})
    except Exception as e:
        weblog.warning(f"error json_template_names {e}")
        return jsonify(list())


@app.route("/internet/isp/total/", methods=['POST', "GET"])
def internet_total_json():
    date_start = '2019-1-1'
    date_end = '2019-1-31'
    percentile = .95
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
               '''.format(initial_date=date_start, end_date=date_end)
    df = pd.read_sql(sql, con=mysql.master.db_connect())
    df["day"] = df["state_timestamp"].apply(lambda x: x.day)

    df2 = df[['host', 'uid', 'inter', 'description', 'l3p', 'l3a', 'l1_protocol', 'data_flow',
              'l1_protocol_attr']].drop_duplicates(subset='uid', keep='first')
    df_proceded = (
        df.groupby(by=['uid', "day"])['util_out', 'util_in', 'out_gbs', 'in_gbs'].quantile(percentile)).round(
        1).reset_index()
    df_merge = pd.merge(df_proceded, df2, on=['uid'], how='left')

    df_merge.drop(['uid'], axis=1, inplace=True)
    df_merge["int_host"] = df_merge["host"] + df_merge["inter"]
    df_merge["x"] = df_merge["day"]
    df_merge["y1"] = df_merge["in_gbs"]
    df_merge["y2"] = df_merge["out_gbs"]
    sort_columns = {'CAPACIDADES_TRANSITO_INTERNET': 'util_in', 'CAPACIDADES_DIRECTOS_ASN': 'util_in',
                    'SERVIDORES_CACHE_TERCEROS': 'util_in',
                    'default': 'util_out'}

    return jsonify(filter_summary(df_merge, ["int_host", "x", "y1", "y2"], sort_column=sort_columns))


def filter_sql(filtro, apply_and=True, table_suffix=""):
    filter_keys = {'CAPACIDADES_TRANSITO_INTERNET': {'l3_protocol_attr': 'IPT'},
                   'CAPACIDADES_DIRECTOS_ASN': {'l3_protocol_attr': 'PNI'},
                   'BGPS_DIRECTOS_INTERNOS_DOWNSTREAM': {'l3_protocol_attr': 'IBP', 'data_flow': 'DOWNSTREAM'},
                   'TRUNCALES_MPLS_DOWNSTREAM': {'l3_protocol': 'MPLS',
                                                 'l1_protocol': 'CABLE_SUBMARINO', 'data_flow': 'DOWNSTREAM'
                                                 },
                   'SERVIDORES_CACHE_TERCEROS': {'l3_protocol_attr': 'CDN'},
                   'PROVEEDORES_TIER_1_INTERNET': {'l3_protocol_attr': 'IPT'},
                   'CONEXIONES_DIRECTAS_PEERING': {'l3_protocol_attr': 'PNI'},
                   'SERVIDORES_CACHE_TERCEROS': {'l3_protocol_attr': 'CDN'},
                   'TRUNCALES_SUBMARINAS_MPLS': {'l3_protocol': 'MPLS',
                                                 'l1_protocol': 'CABLE_SUBMARINO', 'data_flow': 'DOWNSTREAM'
                                                 },
                   'BGPS_DIRECTOS': {'l3_protocol_attr': 'IBP', 'data_flow': 'DOWNSTREAM'}
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
        row = list(row.values())
        try:
            data[str(row[grouping_index])][str(row[column_index])] = float(row[value_index])
        except KeyError as e:
            print("key " + repr(e))
            print(row)
            print(grouping_index, column_index, value_index)
    data2 = [
        {'x': list(serie.keys()), 'y': list(serie.values()), 'name': serie_name, 'stackgroup': 'dos',
         'fill': 'tonexty', 'hoverlabel': {'namelength': -1}}
        for serie_name, serie in data.items()]
    return data2


@app.route('/diagramas/intervalos', methods=['POST', 'GET'])
def diagrama_intervalos_view():
    return render_template('diagramas_intervalos.html')


@app.route('/diagramas/ospf_json_intervalos', methods=['POST', 'GET'])
def diagrama_intervalos_json():
    covertidor = {"guatemala": "RCE_GUATEMALA", "_ospf_ufinet_regional": "_ospf_ufinet_regional"}
    request.get_json()
    network = covertidor[request.json['network']]
    tipo_periodo = request.json['tipo_periodo']
    period_start = request.json['date']
    if period_start == "":
        period_start = str(datetime.datetime.today()).split(' ')[0]

    isp = ISP()
    isp.master = master
    base = datetime.datetime.strptime(period_start, '%Y-%m-%d')
    date_list = [str(base + datetime.timedelta(**{tipo_periodo: x})) for x in range(0, 25)]

    data_red = {
        "_ospf_ufinet_regional": {
            "ip_seed_router": "172.16.30.5", "process_id": '1', "area": '0',
            'network_name': '_ospf_ufinet_regional'
        },
        "RCE_GUATEMALA": {
            "ip_seed_router": "172.17.22.52",
            "process_id": '502', "area": '502008', 'network_name': 'RCE_GUATEMALA'
        }}
    pf = PerformanceLog('24 hours diagram')
    threads = []
    dbs = []
    data_final = []
    for i in range(0, 24):
        period_start = date_list[i]
        period_end = date_list[i + 1]
        dbd = ospf_database(isp=isp, source='delay_start', period_start=period_start, period_end=period_end,
                            **data_red[network])
        dbs.append(dbd)
        t = Thread(target=dbd.delay_start)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    for dbd in dbs:
        data = dbd.get_vs()
        data_final.append({'period': f'{dbd.period_start} - {dbd.period_end}', 'vs': data})
    pf.flag('end')
    pf.print_intervals()

    return jsonify(data_final)


@app.route('/diagramas/save_xy', methods=['POST'])
def save_xy_diagram():
    covertidor = {"guatemala": "RCE_GUATEMALA", "_ospf_ufinet_regional": "_ospf_ufinet_regional"}
    request.get_json()
    network = covertidor[request.json['network']]
    data = request.json['data']
    diagram = Diagram(master=master, name=network)
    diagram.get_newer_state()
    diagram.state.devices()
    diagram.state.save_position(data_devices=data)
    return jsonify({"bueno": "dsd"})


@app.route('/utilidades/metodos/cisco_json', methods=['POST', 'GET'])
def json_cisco_commands_tabulated():
    request.get_json()
    ip = request.json['ip']
    method = request.json['method']
    ufinet = Claro()
    ufinet.master = Master()

    try:
        device = ufinet.correct_device_platform(ufinet.devices_from_ip_list([ip]))[0]
        device.isp = ufinet
        method_instantiated = getattr(device, method)
        dict_table_data = method_instantiated()
        data_json = jsonify(dict_table_data)
        return data_json



    except Exception as e:
        print(repr(e))


@app.route('/utilidades/metodos/cisco')
def tabulate_cisco_command():
    return render_template('cisco_tabulated_method.html')


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
    pl = PerformanceLog("json")
    sql = '''select  
        CONCAT(d.hostname, " > ", i.if_index) AS int_host ,
        DATE(s.state_timestamp) as date_poll,
        max((s.{3}_rate/1000000000)) as value_request ,
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
        order BY value_request DESC, date_poll ASC
        
        ;
        '''.format(date_start, date_end, sql_text, in_out)
    with master.db_connect().cursor() as cursor:
        cursor.execute(sql)
        data_sql = cursor.fetchall()
        pl.new_flag("load normal sql")
        data = function_pivot(data_sql)
        pl.new_flag("pivot")

    jdata = jsonify(data)
    pl.new_flag("j data")
    pl.new_flag("end")
    if (pl.time_flag() > 2000):
        per.warning("JSON_GRAPH TO MUCH TIME " + pl.format_time_lapse())
    else:
        per.debug("JSON_GRAPH " + pl.format_time_lapse())
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
                                                 'l1_protocol': 'CABLE_SUBMARINO', 'data_flow': 'DOWNSTREAM'
                                                 },
                   'SERVIDORES_CACHE_TERCEROS': {'l3a': 'CDN'}
                   }
    results = {}
    verbose.warning(f'columns dataframe {sql_dataframe.columns}')
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
    app.run(port=port, host=host, debug=True, threaded=True)
