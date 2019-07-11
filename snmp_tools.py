import asyncio
from pysnmp.hlapi.asyncio import *


@asyncio.coroutine
def run(data):
    errorIndication, errorStatus, errorIndex, varBinds = yield from bulkCmd(
        UsmUserData('usr-md5-none', 'authkey1'),
        UdpTransportTarget(('demo.snmplabs.com', 161)),
        ContextData(),
        0, 3,
        ObjectType(ObjectIdentity('SNMPv2-MIB', 'system')),
    )
    data.append(varBinds)
    print(errorIndication, errorStatus, errorIndex, varBinds)


data = []
asyncio.get_event_loop().run_until_complete(run(data))
