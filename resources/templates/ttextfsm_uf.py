import textfsm
from pprint import pprint

fsm = textfsm.TextFSM(open("show mpls l2transport vc detail ios.template"))
file_data = open("../output_test/show mpls l2transport vc detail ios").read()
fsm_results = fsm.ParseText(file_data, )

print(fsm.header)
values = [dict(zip(fsm.header, row)) for row in fsm_results]

data = [row for row in fsm_results]
pprint(values)
# pprint(fsm_results)
