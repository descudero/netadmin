import textfsm
from pprint import pprint

fsm = textfsm.TextFSM(open("show inventory.template"))
file_data = open("../output_test/show inventory XE").read()
fsm_results = fsm.ParseText(file_data, )

print(fsm.header)
values = [dict(zip(fsm.header, row)) for row in fsm_results]

data = [row for row in fsm_results]
pprint(values)
pprint(len(fsm_results))
