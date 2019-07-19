import asyncio
from pysnmp.hlapi.asyncio import *
import time


def cast(value):
    try:
        if "IpAddress" in str(value.__class__):
            data = [str(val) for val in map(ord, str(value))]
            return ".".join(data)
    except Exception as e:
        print(f"error casting ip {e}")
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return float(value)
        except (ValueError, TypeError):
            try:
                return str(value)
            except (ValueError, TypeError):
                pass
    return value


async def snmp_walk(ip, oid, community, id_ip=False):
    varBinds = [ObjectType(ObjectIdentity(oid))]
    results = []
    # print(ip)
    snmpEngine = SnmpEngine()
    initialVarBinds = varBinds
    break_flag = True
    while break_flag:

        (errorIndication, errorStatus, errorIndex, varBindTable) = await nextCmd(
            snmpEngine,
            CommunityData(community),
            UdpTransportTarget((ip, 161)),
            ContextData(),
            *varBinds,
            lexicographicMode=False
        )
        timestamp = time.time()
        if errorIndication:
            print(errorIndication)
            break
        elif errorStatus:
            print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'
            )
                  )
        else:

            for varBindRow in varBindTable:
                for idx, varBind in enumerate(varBindRow):
                    oid_flat = str(varBind[0]).replace(f'{oid}.', '')
                    try:
                        value = cast(varBind[1])
                    except Exception as e:
                        print(f'error casting value {value} v:{value.__class__}')
                        value = "na"
                    items = {"id": oid_flat, "value": value, "timestamp": timestamp, "ip_parent": ip}
                    try:
                        if "." in oid_flat and not id_ip or (id_ip and oid_flat.count(".") > 3):
                            break_flag = False

                        else:
                            results.append(items)
                        # pprint(items)
                    except Exception as e:
                        print(f'checking   {oid} {e}')

        varBinds = varBindTable[-1]
        if isEndOfMib(varBinds):
            break
        for varBind in varBinds:
            if initialVarBinds[0][idx].isPrefixOf(varBind[0]):
                break

        else:
            break
    snmpEngine.transportDispatcher.closeDispatcher()
    return results


async def main():
    loop = asyncio.get_event_loop()
    ips = ['172.16.30.244', '172.16.30.246', '172.16.30.248', '172.16.30.250', '172.16.30.251']
    tasks = []
    for ip in ips:
        tasks.append(loop.create_task(snmp_walk(ip, oid='1.3.6.1.2.1.31.1.1.1.6', community='uFi08NeT')))

    final_data = []
    for task in tasks:
        data = await task
        final_data.append(data)

    print(final_data)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
