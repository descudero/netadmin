import requests
import urllib
from threading import Thread
import threading as th


def function_test(id):
    session = requests.Session()
    payload = {'username': 'nocuser', 'password': 'NocL@tam92017'}
    url = 'https://prtgla.ufinetlatam.net/public/checklogin.htm'
    p = session.post(url, data=payload)

    r = session.get(
        'https://prtgla.ufinetlatam.net/historicdata_html.htm?id=' + str(
            id) + '&sdate=2018-06-01-15-50-00&edate=2018-07-01-15-50-00&avg=3600&pctavg=300&pctshow=true&pct=95&pctmode=false')
    print("id " + id)
    print("data " + (r.text.split("<td class=title>Percentile")[1].split(" Mbit/s")[0].split(">")[-1].replace(",", "")))
    return ((r.text.split("<td class=title>Percentile")[1].split(" Mbit/s")[0].split(">")[-1].replace(",", "")))


th.Thread()
ready_devices = []
id_list = ['4865', '4866', '4951']
id_lista = ['4954', '4870', '5043', '5044']
threads = []
for id in id_list:
    t = th.Thread(target=function_test, kwargs={"id": id})
    t.start()
for t in threads:
    t.join()
threads = []
for id in id_lista:
    t = th.Thread(target=function_test, kwargs={"id": id})
    t.start()
for t in threads:
    t.join()
