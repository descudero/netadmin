# imports
import collections
import getpass;
from collections import defaultdict

from config.Master import Master
from model.CiscoXR import CiscoXR

master = Master(password=Master.decode("ufinet", "w4rDjMOSw5zDisOowqbCnsOI"),
                username=Master.decode("pinf con vrf", "w5fDjsOhw5rCicOSw50="))

# pba = CiscoDevice("PBAIPP",'C:\\Users\\descudero\\pba.txt')
# blu = CiscoDevice("BLUIPP",'C:\\Users\\descudero\\blu.txt')
# gdv = CiscoDevice("GDVIPP",'C:\\Users\\descudero\\gdv.txt')
##print(cisco.interfaces)
# print(cisco.route_policies)
# print(cisco.prefix_sets)
# interfaces = pba.route_policy_perInterface()

pba = CiscoXR("10.192.0.27", "pba", master)
blu = CiscoXR("10.192.0.146", "blu", master)
gdv = CiscoXR("10.192.0.22", "gdv", master)

prefixPass = {}


def recursive_defaultdict():
    return defaultdict(recursive_defaultdict)


def setpath(d, p, k):
    if len(p) == 1:
        d[p[0]] = k
    else:
        setpath(d[p[0]], p[1:], k)


prefixes = recursive_defaultdict()

ipps = {"pba": {"cisco": pba}, "blu": {"cisco": blu}, "gdv": {"cisco": gdv}}

for nameIpp, ipp in ipps.items():
    policyInterface = ipp["cisco"].route_policy_per_interface()
    for interface, policy in policyInterface.items():
        sequences = policy.filterAction(["pass"])
        for sequence in sequences:
            print(sequence[["condition"][0]]["pass"]["pass"][nameIpp][policy.name][interface])
            prefixes[sequence["condition"][0]]["pass"]["pass"][nameIpp][policy.name][interface] = 1;

prepends = ["prepend as-path 14754 2 ",
            "prepend as-path 14754 10",
            "prepend as-path 14754 6",
            "prepend as-path 14754 5",
            "prepend as-path 14754 4",
            "prepend as-path 14754 8",
            "prepend as-path 14754 12"
    , "prepend as-path 14754 20"]

for prepend in prepends:
    for nameIpp, ipp in ipps.items():
        policyInterface = ipp["cisco"].route_policy_per_interface()
        for interface, policy in policyInterface.items():
            sequences = policy.filterAction([prepend])
            for sequence in sequences:
                prefixes[sequence["condition"][0]]["prepend"][prepend][nameIpp][policy][interface] = 1;

prefixes2 = collections.OrderedDict(sorted(prefixes.items()))
print("Prefix name,action,sub action, ipp, policy")
for prefix, ipps in prefixes2.items():
    # print(prefix)
    for ipp, actions in ipps.items():
        #    print("\t",ipp)
        for action, subactions in actions.items():
            #       print("\t\t", action)
            for subaction, policies in subactions.items():
                #          print("\t\t\t", subaction)
                for policy, interfaces in policies.items():
                    print(prefix, ",", ipp, ",", action, ",", subaction, ",", policy.name)
            # for interface, value in interfaces.items():

            #    print("\t\t\t",interface)
# print()
# print("gdv")
print(gdv.print_prefix())
# print()
# print("pba")
print(pba.print_prefix())
# print()
# print("blu")
print(blu.print_prefix())

getpass._raw_input(prompt=' presionar para terminar  ')
