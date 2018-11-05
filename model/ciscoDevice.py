from model.RoutePolicy import RoutePolicy
from model.prefixSet import PrefixSet


class CiscoDevice:

    def __init__(self, name, url):
        self.name = name
        Archivo = open(url, 'r')
        self.lineasConfig = Archivo.readlines()
        self.parsearInterfaces()
        self.parsearRoutePolicy()
        self.parsearPrefixSet()

    def parsearInterfaces(self):
        lineas = self.lineasConfig
        interfaces = {};
        for index, linea in enumerate(lineas):
            if (linea.startswith("interface")):
                if (index + 1 < len(lineas)):
                    if (lineas[index + 1].startswith(" description")):
                        if (lineas[index + 1].find("PEER:") != -1):
                            # description TAG:ROJO ! CP:40GB ! EBGP:COGENT ! PEER:38.88.165.53 !
                            #  EBGPID:CIRCUIT-ID 1-300032199 ! TX:AMX ! TXID:CABLE AMX-1 -REMOTE EQ ROUTER
                            # 21.MIA03 ID-AMX IAM1GTIZPPBR-USFLMNAP-GE10-005
                            descripcion = lineas[index + 1].replace(" description", "").replace("\n", "")
                            datos = descripcion.split("!")
                            tag = datos[0].replace("TAG:", "").replace(" ", "")
                            capacidad = datos[1].replace("CP:", "").replace(" ", "")
                            ebgp = datos[2].replace("EBGP:", "").replace(" ", "")
                            peer = datos[3].replace("PEER:", "").replace(" ", "")
                            ebgpid = datos[4].replace("EBGPID:", "").replace(" ", "")
                            tx = datos[5].replace("TX:", "").replace(" ", "")
                            txid = datos[6].replace("TXID:", "")
                            Index = linea.replace("interface ", "").replace(" ", "").replace("\n", "")
                            Interfaz = Interfaz(Index, descripcion, tag, peer, ebgp, ebgpid, tx, txid)
                            interfaces[Index] = Interfaz
        self.interfaces = interfaces

    def parsearRoutePolicy(self):
        lineas = self.lineasConfig
        routemaps = {}
        index = 0
        inPolicy = False
        conditionPoilicyflag = False
        policy = RoutePolicy("incial")
        for index in range(0, len(lineas)):

            if (lineas[index].startswith("route-policy")):
                namePolicy = lineas[index].replace("route-policy ", "").replace("\n", "")
                inPolicy = True
                policy = RoutePolicy(namePolicy)
            else:
                if (inPolicy):
                    if (lineas[index].startswith("  if") or lineas[index].startswith("  elseif")):
                        conditionPolicy = lineas[index].replace("  if ", "").replace(" then", "").replace("  elseif ",
                                                                                                          "").replace(
                            "\n", "")

                        if (lineas[index + 1].startswith("    drop")
                                or lineas[index + 1].startswith("    pass")
                                or lineas[index + 1].startswith("    prepend")
                                or lineas[index + 1].startswith("    apply")):
                            actionPolicy = lineas[index + 1].replace("\n", "").replace("    ", "")
                            policy.setSequence(conditionPolicy, actionPolicy)

                    else:
                        if (lineas[index].startswith("  endif")):
                            inPolicy = False
                            routemaps[policy.name] = policy
        self.routePolicies = routemaps

    def parsearPrefixSet(self):
        # metodo agrega los prefix a la propiedad
        lineas = self.lineasConfig
        prefisets = {}
        index = 0
        inPrefix = False
        prefixset = PrefixSet("inicial")
        for index in range(0, len(lineas)):
            if (inPrefix):
                if (lineas[index].find("#") == -1):
                    if (lineas[index].find("end-set") != -1):
                        inPrefix = False
                        prefisets[prefixset.name] = prefixset
                    else:
                        prefixset.setSequence(lineas[index].replace("  ", "").replace(",", "").replace("\n", ""))

            else:
                if (lineas[index].startswith("prefix-set")):
                    prefixset = PrefixSet(lineas[index].replace("prefix-set ", "").replace("\n", ""))
                    inPrefix = True

        self.prefixSets = prefisets

    def routePolicyPerInterface(self):
        policyInterface = {}
        for key, interface in self.interfaces.items():

            namePolicy = self.searchRoutePolicy(interface.peer.replace(".", "_"))
            policy = self.routePolicies[namePolicy]
            if (policy.hasApply() != 0):
                namePolicy = policy.hasApply()
            policyInterface[key] = self.routePolicies[namePolicy];
        return policyInterface

    def searchRoutePolicy(self, contains):
        match = ""
        for key, policy in self.routePolicies.items():
            if (key.find(contains) != -1 and key.find("out") != -1):
                return key

        return False;

    def printPrefix(self):
        result = ""
        for key, prefix in self.prefixSets.items():
            result += prefix.printTable();
        return result
