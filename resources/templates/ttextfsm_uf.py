import textfsm
from pprint import pprint

fsm = textfsm.TextFSM(open("show ip ospf database router.template"))
file_data = open("../output_test/show ip ospf database router").read()
fsm_results = fsm.ParseText(file_data, )

print(fsm.header)
values = [dict(zip(fsm.header, row)) for row in fsm_results]

data = [row for row in fsm_results]
pprint(values)
# pprint(fsm_results)
