import ipaddress


class PrefixSet(object):
    def __init__(self, name):
        self.name = name
        self.prefixes = []
        self.parentsPolicy = []

    def setParentPolicy(self, parent):
        self.parentsPolicy.append(parent)

    def setSequence(self, prefix):
        network = ipaddress.ip_network(prefix.split(" ")[0], strict=False)
        tuple = {"network": network, "string": prefix}
        self.prefixes.append(tuple)

    def printTable(self):
        result = ""
        # print("name "+ self.name)
        for network in self.prefixes:
            result += (self.name + "\t" + network["string"] + " " + str(network["network"]) + "\n")
        return result

    def ipInPrefixSet(self, stringIp):
        stringIp = stringIp.replace(" ", "")
        add = ipaddress.ip_address(stringIp)

        for prefix in self.prefixes:
            if add in prefix["network"]:
                return True
        return False

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name
